import json
import os

import google.generativeai as genai
from groq import Groq

from rag.retriever import retrieve_jd_context, retrieve_resume_context

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

QUESTION_MIX = {
    "behavioral": 3,
    "technical": 3,
    "situational": 1,
    "resume_deep_dive": 1,
}

TYPE_INSTRUCTIONS = {
    "behavioral": (
        "This MUST be a BEHAVIORAL question. Use STAR-format phrasing: "
        '"Tell me about a time when..." or "Describe a situation where...". '
        "It asks about a PAST experience."
    ),
    "technical": (
        "This MUST be a TECHNICAL question. Ask directly about a specific skill or "
        'technology from the JD — e.g. "How would you design...", "What\'s the '
        'difference between...", "Walk me through how you\'d implement...". '
        'Do NOT phrase it as "Tell me about a time" — that is a behavioral question, '
        "not this one."
    ),
    "situational": (
        "This MUST be a SITUATIONAL question. Present a hypothetical, forward-looking "
        'scenario or trade-off — e.g. "What would you do if...", "How would you '
        'handle...". Do NOT phrase it as "Tell me about a time" — this is about a '
        "hypothetical future scenario, not a past experience."
    ),
    "resume_deep_dive": (
        "This MUST be a RESUME_DEEP_DIVE question. Pick a specific project or "
        "experience named in the candidate's resume above and ask a probing "
        "follow-up question about it specifically."
    ),
}

PROMPT_TEMPLATE = """You are a senior technical interviewer at a top-tier tech company.

Candidate Resume Context:
{resume_context}

Job Description Requirements:
{jd_context}

Generate exactly ONE interview question of type "{question_type}" for this candidate and role.

{type_instruction}

Respond ONLY with valid JSON, no markdown, no explanation:
{{
  "question": "...",
  "expected_themes": ["theme1", "theme2", "theme3"],
  "difficulty": "easy|medium|hard",
  "question_type": "{question_type}"
}}"""


def _build_prompt(resume_context: str, jd_context: str, question_type: str) -> str:
    return PROMPT_TEMPLATE.format(
        resume_context=resume_context,
        jd_context=jd_context,
        question_type=question_type,
        type_instruction=TYPE_INSTRUCTIONS[question_type],
    )


def call_gemini(prompt: str) -> dict:
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return json.loads(response.text.strip())


def call_groq_fallback(prompt: str) -> dict:
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return json.loads(response.choices[0].message.content.strip())


def _generate_single(resume_context: str, jd_context: str, question_type: str) -> dict:
    prompt = _build_prompt(resume_context, jd_context, question_type)
    try:
        result = call_gemini(prompt)
        result["source"] = "gemini"
        return result
    except Exception as e:
        print(f"[Gemini failed] {e} — falling back to Groq")
        result = call_groq_fallback(prompt)
        result["source"] = "groq"
        return result


def get_question_plan() -> list[str]:
    """Expand QUESTION_MIX into a flat ordered list of question types to generate."""
    return [qtype for qtype, count in QUESTION_MIX.items() for _ in range(count)]


def get_contexts(session_id: str, role: str) -> tuple[str, str]:
    resume_context = "\n\n".join(retrieve_resume_context(session_id, role, n=5))
    jd_context = "\n\n".join(retrieve_jd_context(session_id, role, n=5))
    return resume_context, jd_context
