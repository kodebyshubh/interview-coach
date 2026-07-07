import uuid
from unittest.mock import patch

import pytest

from db.models import Answer


MOCK_SUMMARY = {
    "overall_score": 6.4,
    "performance_band": "decent",
    "one_line_verdict": "Solid foundation but needs depth in system design.",
    "top_strengths": [{"topic": "communication", "evidence": "Clear and structured answers."}],
    "top_weaknesses": [
        {"topic": "system design", "pattern": "surface level", "action": "Read DDIA ch1-3"}
    ],
    "question_type_analysis": {
        "behavioral": "strong",
        "technical": "needs work",
        "situational": "decent",
        "resume_deep_dive": "strong",
    },
    "recommended_resources": [
        {"title": "DDIA", "type": "concept", "reason": "For system design depth"}
    ],
    "computed_stats": {
        "avg_score": 6.4,
        "type_breakdown": {"behavioral": 7.0},
        "top_weak_topics": ["system design"],
    },
}

LONG_ANSWER = "I designed and implemented a distributed caching layer that reduced our API response times by 60 percent."


async def _make_answers(db, test_session, test_question, count=3, is_probe=False):
    answers = []
    for i in range(count):
        a = Answer(
            id=uuid.uuid4(),
            question_id=test_question.id,
            session_id=test_session.id,
            text=f"Answer {i}: {LONG_ANSWER}",
            score=6 + i,
            feedback="Good answer.",
            weak_topics=[],
            is_probe=is_probe,
        )
        db.add(a)
        answers.append(a)
    await db.commit()
    return answers


async def test_summarize_session_success(client, test_session, test_question, db):
    await _make_answers(db, test_session, test_question, count=3)

    with patch("agents.summarizer.call_gemini_summary", return_value=MOCK_SUMMARY):
        response = await client.post(f"/api/session/{test_session.id}/summarize")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == str(test_session.id)
    assert "summary" in data


async def test_summarize_no_answers(client, test_session):
    response = await client.post(f"/api/session/{test_session.id}/summarize")
    assert response.status_code == 400


async def test_summarize_too_few_answers(client, test_session, test_question, db):
    await _make_answers(db, test_session, test_question, count=2)

    with patch("agents.summarizer.call_gemini_summary", return_value=MOCK_SUMMARY):
        response = await client.post(f"/api/session/{test_session.id}/summarize")

    assert response.status_code == 400
    assert "2" in response.json()["detail"]


async def test_summarize_excludes_probe_answers(client, test_session, test_question, db):
    await _make_answers(db, test_session, test_question, count=3, is_probe=False)
    await _make_answers(db, test_session, test_question, count=2, is_probe=True)

    with patch("agents.summarizer.call_gemini_summary", return_value=MOCK_SUMMARY) as mock_llm:
        response = await client.post(f"/api/session/{test_session.id}/summarize")

    assert response.status_code == 200
    call_args = mock_llm.call_args[0][0]  # prompt string
    # Probe answers scored but excluded — only 3 non-probe answers in prompt
    assert "Q3" in call_args
    assert "Q4" not in call_args  # 4th item would be a probe


async def test_get_session_progress(client, test_session, test_answer):
    response = await client.get(f"/api/session/{test_session.id}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["average_score"] == 7.0
    assert data["answers_submitted"] == 1
    assert len(data["scores"]) == 1


async def test_get_session_progress_no_answers(client, test_session):
    response = await client.get(f"/api/session/{test_session.id}/summary")
    assert response.status_code == 404


async def test_summary_contains_required_keys(client, test_session, test_question, db):
    await _make_answers(db, test_session, test_question, count=3)

    with patch("agents.summarizer.call_gemini_summary", return_value=MOCK_SUMMARY):
        response = await client.post(f"/api/session/{test_session.id}/summarize")

    summary = response.json()["summary"]
    required = [
        "overall_score", "performance_band", "top_strengths", "top_weaknesses",
        "recommended_resources", "one_line_verdict", "computed_stats",
    ]
    for key in required:
        assert key in summary, f"Missing key: {key}"


async def test_summarize_invalid_session(client):
    response = await client.post(f"/api/session/{uuid.uuid4()}/summarize")
    assert response.status_code == 404
