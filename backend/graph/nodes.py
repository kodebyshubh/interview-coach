import json
import time

from agents.evaluator import evaluate_answer
from agents.probe_generator import generate_probe
from agents.question_generator import _build_prompt, _generate_single, groq_client
from agents.summarizer import generate_session_summary
from mcp_tools.question_bank_client import call_get_bank_question, list_bank_tools_openai_format

from .state import InterviewState


def _timed(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    latency_ms = int((time.perf_counter() - start) * 1000)
    return result, latency_ms


def _generate_with_bank_tool(resume_context: str, jd_context: str, question_type: str, role: str) -> dict:
    """Groq call with the question-bank MCP tool bound — the LLM genuinely chooses
    whether to call get_bank_question (cheap, canned) or write a fresh question,
    based on the tool's own description. Real tool binding, not a hardcoded call:
    if the model doesn't emit a tool_call, we just parse its plain JSON response."""
    prompt = _build_prompt(resume_context, jd_context, question_type)
    tools = list_bank_tools_openai_format()

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You can call get_bank_question if a good pre-written question already "
                    "exists for this exact role and question_type — prefer it for common, "
                    "generic combinations since it's free and instant. Otherwise write a new "
                    "question yourself, following the instructions in the user message."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        tools=tools,
        tool_choice="auto",
        temperature=0.7,
    )
    message = response.choices[0].message

    if message.tool_calls:
        call = message.tool_calls[0]
        args = json.loads(call.function.arguments)
        result = call_get_bank_question(args.get("role", role), args.get("question_type", question_type))
        result["source"] = "mcp_bank"
        return result

    result = json.loads(message.content.strip())
    result["source"] = "groq"
    return result


def interviewer_node(state: InterviewState) -> dict:
    """Generates the next planned question, or a probe follow-up.

    Plan-driven generation (question_plan non-empty) and probe generation
    are the two things an interviewer does — distinguished by which state
    is present, not by a separate node.
    """
    if state.get("question_plan"):
        plan = list(state["question_plan"])
        question_type = plan.pop(0)

        try:
            result, latency_ms = _timed(
                _generate_with_bank_tool,
                state["resume_context"], state["jd_context"], question_type, state["role"],
            )
        except Exception as e:
            print(f"[Tool-aware generation failed] {e} — falling back to standard generation")
            try:
                result, latency_ms = _timed(
                    _generate_single, state["resume_context"], state["jd_context"], question_type
                )
            except Exception as e2:
                print(f"[Standard generation failed] {e2} — falling back directly to question bank")
                start = time.perf_counter()
                result = call_get_bank_question(state["role"], question_type)
                result["source"] = "mcp_bank_fallback"
                latency_ms = int((time.perf_counter() - start) * 1000)

        result["session_id"] = state["session_id"]
        questions = state.get("questions", []) + [result]
        log_entries = state.get("log_entries", []) + [{
            "question_id": None,
            "question_text": result.get("question"),
            "answer_text": None,
            "score": None,
            "latency_ms": latency_ms,
            "model_used": result.get("source", "unknown"),
        }]
        return {"question_plan": plan, "questions": questions, "log_entries": log_entries}

    evaluation = state["evaluation"]
    latency_ms = 0
    try:
        probe, latency_ms = _timed(
            generate_probe,
            original_question=state["question"]["text"],
            answer_text=state["answer_text"],
            weak_topics=evaluation.get("weak_topics", []),
            feedback=evaluation["feedback"],
        )
    except Exception as e:
        print(f"[Probe generation failed] {e} — skipping probe")
        probe = None

    log_entries = state.get("log_entries", [])
    if probe is not None:
        log_entries = log_entries + [{
            "question_id": None,
            "question_text": state["question"]["text"],
            "answer_text": state["answer_text"],
            "score": None,
            "latency_ms": latency_ms,
            "model_used": probe.get("source", "unknown"),
        }]
    return {"probe": probe, "log_entries": log_entries}


def evaluator_node(state: InterviewState) -> dict:
    question = state["question"]
    evaluation, latency_ms = _timed(
        evaluate_answer,
        question_text=question["text"],
        question_type=question["question_type"],
        expected_themes=question.get("expected_themes") or [],
        answer_text=state["answer_text"],
    )
    needs_probe = bool(evaluation.get("needs_probe")) and not state.get("is_probe", False)
    log_entries = state.get("log_entries", []) + [{
        "question_id": None,
        "question_text": question["text"],
        "answer_text": state["answer_text"],
        "score": evaluation.get("overall_score"),
        "latency_ms": latency_ms,
        "model_used": evaluation.get("source", "unknown"),
    }]
    return {"evaluation": evaluation, "needs_probe": needs_probe, "log_entries": log_entries}


def feedback_node(state: InterviewState) -> dict:
    summary, latency_ms = _timed(
        generate_session_summary, role=state["role"], answers=state["answers"]
    )
    log_entries = state.get("log_entries", []) + [{
        "question_id": None,
        "question_text": None,
        "answer_text": None,
        "score": None,
        "latency_ms": latency_ms,
        "model_used": summary.get("source", "unknown"),
    }]
    return {"summary": summary, "log_entries": log_entries}
