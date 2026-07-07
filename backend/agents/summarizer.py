import json
import os
from collections import Counter

import google.generativeai as genai
from groq import Groq

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SUMMARY_PROMPT_TEMPLATE = """You are an expert career coach reviewing a completed mock interview session.

Role Interviewed For: {role}

Interview Results:
{answers_block}

Aggregate Stats:
- Total questions answered: {total_answers}
- Average score: {avg_score}/10
- Score breakdown by question type: {type_breakdown}
- Most common weak topics across all answers: {top_weak_topics}

Based on this data, generate a structured post-interview report.

Respond ONLY with valid JSON, no markdown, no preamble:
{{
  "overall_score": <float, one decimal>,
  "performance_band": "poor|needs_work|decent|strong|excellent",
  "top_strengths": [
    {{"topic": "...", "evidence": "one specific thing they did well"}}
  ],
  "top_weaknesses": [
    {{
      "topic": "...",
      "pattern": "what kept going wrong",
      "action": "one concrete thing to do this week to fix it"
    }}
  ],
  "question_type_analysis": {{
    "behavioral": "brief verdict",
    "technical": "brief verdict",
    "situational": "brief verdict",
    "resume_deep_dive": "brief verdict"
  }},
  "recommended_resources": [
    {{"title": "...", "type": "concept|practice|framework", "reason": "..."}}
  ],
  "one_line_verdict": "A single honest sentence summarizing this candidate's readiness."
}}"""


def _build_answers_block(answers: list) -> str:
    lines = []
    for i, a in enumerate(answers, 1):
        lines.append(
            f"Q{i} [{a['question_type']}] (score: {a['score']}/10)\n"
            f"  Question: {a['question_text']}\n"
            f"  Answer: {a['answer_text'][:300]}{'...' if len(a['answer_text']) > 300 else ''}\n"
            f"  Feedback: {a['feedback']}\n"
            f"  Weak topics: {', '.join(a['weak_topics']) if a['weak_topics'] else 'none'}"
        )
    return "\n\n".join(lines)


def compute_stats(answers: list) -> dict:
    scores = [a["score"] for a in answers if a["score"] is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    type_scores: dict[str, list] = {}
    for a in answers:
        qt = a["question_type"]
        if qt not in type_scores:
            type_scores[qt] = []
        if a["score"] is not None:
            type_scores[qt].append(a["score"])

    type_breakdown = {
        qt: round(sum(s) / len(s), 1)
        for qt, s in type_scores.items()
        if s
    }

    all_weak_topics = []
    for a in answers:
        if a["weak_topics"]:
            all_weak_topics.extend(a["weak_topics"])

    top_weak_topics = [topic for topic, _ in Counter(all_weak_topics).most_common(5)]

    return {
        "avg_score": avg_score,
        "type_breakdown": type_breakdown,
        "top_weak_topics": top_weak_topics,
    }


def call_gemini_summary(prompt: str) -> dict:
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return json.loads(response.text.strip())


def call_groq_summary_fallback(prompt: str) -> dict:
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return json.loads(response.choices[0].message.content.strip())


def generate_session_summary(role: str, answers: list) -> dict:
    """Gemini primary (reasoning-heavy report), Groq fallback. Attaches computed_stats."""
    stats = compute_stats(answers)
    answers_block = _build_answers_block(answers)

    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        role=role,
        answers_block=answers_block,
        total_answers=len(answers),
        avg_score=stats["avg_score"],
        type_breakdown=json.dumps(stats["type_breakdown"]),
        top_weak_topics=", ".join(stats["top_weak_topics"]) or "none identified",
    )

    try:
        result = call_gemini_summary(prompt)
        result["source"] = "gemini"
    except Exception as e:
        print(f"[Gemini summary failed] {e} — falling back to Groq")
        result = call_groq_summary_fallback(prompt)
        result["source"] = "groq"

    result["computed_stats"] = stats
    return result
