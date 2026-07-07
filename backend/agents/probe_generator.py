import json
import os

import google.generativeai as genai
from groq import Groq

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROBE_PROMPT_TEMPLATE = """You are a senior interviewer. The candidate gave a weak answer to the following question.

Original Question: {original_question}
Candidate's Answer: {answer}
Weak Topics Identified: {weak_topics}
Evaluator Feedback: {feedback}

Generate a single focused follow-up probe question that:
- Targets the weakest specific gap identified
- Gives the candidate a chance to recover or go deeper
- Is direct, not leading (don't give away the answer)
- Is 1 sentence max

Respond ONLY with valid JSON:
{{
  "probe_question": "...",
  "targets": "the specific gap this probe addresses"
}}"""


def _call_gemini_probe(prompt: str) -> dict:
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return json.loads(response.text.strip())


def _call_groq_probe(prompt: str) -> dict:
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return json.loads(response.choices[0].message.content.strip())


def generate_probe(
    original_question: str, answer_text: str, weak_topics: list, feedback: str
) -> dict:
    """Gemini primary for probe generation (reasoning-heavy), Groq fallback."""
    prompt = PROBE_PROMPT_TEMPLATE.format(
        original_question=original_question,
        answer=answer_text,
        weak_topics=", ".join(weak_topics) if weak_topics else "general weakness",
        feedback=feedback,
    )
    try:
        result = _call_gemini_probe(prompt)
        result["source"] = "gemini"
        return result
    except Exception as e:
        print(f"[Probe Gemini failed] {e} — falling back to Groq")
        result = _call_groq_probe(prompt)
        result["source"] = "groq"
        return result
