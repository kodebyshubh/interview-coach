import json
import os

import google.generativeai as genai
import ollama
from groq import Groq

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# localhost works for local (non-Docker) dev; the containerized backend overrides this
# to http://host.docker.internal:11434 in docker-compose.yml, since Ollama runs on the
# host machine, not as a compose service, and localhost inside the container's network
# namespace does not resolve to the host.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_client = ollama.Client(host=OLLAMA_HOST)

OLLAMA_EVAL_MODEL = "qwen2.5-coder:7b"

EVAL_PROMPT_TEMPLATE = """You are an expert technical interview evaluator. Be honest and specific — not encouraging.

Interview Question: {question}
Question Type: {question_type}
Expected Themes to Cover: {expected_themes}

Candidate's Answer:
{answer}

Evaluate strictly on these 4 dimensions (score each 0-10):
- clarity: Is the answer well-structured and easy to follow?
- depth: Does it show genuine understanding, not just surface knowledge?
- relevance: Does it actually answer the question asked?
- examples: Are concrete, specific examples used? (for behavioral/situational, this is critical)

Then:
- overall_score: integer 0-10 (weighted average, round down)
- feedback: 2-3 sentences of direct, actionable feedback
- weak_topics: list of specific topics the candidate clearly struggled with (empty list if none)
- needs_probe: this is a STRICT NUMERIC RULE, not a judgment call. Set it to exactly
  (overall_score < 6). If overall_score is 6 or higher, needs_probe MUST be false. If
  overall_score is below 6, needs_probe MUST be true. Do not weigh whether the topic
  seems "recoverable" — compute this field mechanically from overall_score alone.

Respond ONLY with valid JSON, no markdown, no preamble:
{{
  "scores": {{
    "clarity": 0,
    "depth": 0,
    "relevance": 0,
    "examples": 0
  }},
  "overall_score": 0,
  "feedback": "...",
  "weak_topics": [],
  "needs_probe": false
}}"""


def _build_eval_prompt(
    question_text: str, question_type: str, expected_themes: list, answer_text: str
) -> str:
    return EVAL_PROMPT_TEMPLATE.format(
        question=question_text,
        question_type=question_type,
        expected_themes=", ".join(expected_themes) if expected_themes else "None specified",
        answer=answer_text,
    )


def call_groq_eval(prompt: str) -> dict:
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content.strip())


def call_gemini_eval_fallback(prompt: str) -> dict:
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return json.loads(response.text.strip())


def call_ollama_eval(prompt: str) -> dict:
    response = ollama_client.chat(
        model=OLLAMA_EVAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )
    return json.loads(response["message"]["content"].strip())


def evaluate_answer(
    question_text: str, question_type: str, expected_themes: list, answer_text: str
) -> dict:
    """Groq primary (fast, blocks the UI per answer), Gemini fallback, Ollama last-resort
    fallback (local, no external quota/availability dependency — see call_ollama_eval)."""
    prompt = _build_eval_prompt(question_text, question_type, expected_themes, answer_text)

    try:
        result = call_groq_eval(prompt)
        result["source"] = "groq"
    except Exception as e:
        print(f"[Groq eval failed] {e} — falling back to Gemini")
        try:
            result = call_gemini_eval_fallback(prompt)
            result["source"] = "gemini"
        except Exception as e2:
            print(f"[Gemini eval failed] {e2} — falling back to Ollama")
            result = call_ollama_eval(prompt)
            result["source"] = "ollama"

    # needs_probe is a deterministic function of overall_score — compute it in code
    # rather than trust the model's own copy of this field. The prompt still asks the
    # model for it (keeps its feedback/reasoning internally consistent), but this
    # overrides whatever it returns so the threshold can never drift from < 6.
    result["needs_probe"] = result["overall_score"] < 6
    return result
