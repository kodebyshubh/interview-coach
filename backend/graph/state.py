from typing import TypedDict


class InterviewState(TypedDict, total=False):
    """Shared state passed through the LangGraph graph.

    Not every field is populated on every invoke — which fields are set
    depends on `stage` (generate_questions / submit_answer / summarize).
    """

    stage: str  # "generate_questions" | "submit_answer" | "summarize"

    # generate_questions
    session_id: str
    role: str
    resume_context: str
    jd_context: str
    question_plan: list[str]
    questions: list[dict]

    # submit_answer
    question: dict
    answer_text: str
    is_probe: bool
    evaluation: dict
    needs_probe: bool
    probe: dict | None

    # summarize
    answers: list[dict]
    summary: dict

    # eval logging — accumulated across every node that makes an LLM call
    log_entries: list[dict]
