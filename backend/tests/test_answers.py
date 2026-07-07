import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select

from db.models import Answer


GOOD_EVAL = {
    "scores": {"clarity": 8, "depth": 7, "relevance": 9, "examples": 7},
    "overall_score": 7,
    "feedback": "Strong answer with good examples.",
    "weak_topics": [],
    "needs_probe": False,
}

WEAK_EVAL = {
    "scores": {"clarity": 4, "depth": 3, "relevance": 5, "examples": 2},
    "overall_score": 4,
    "feedback": "Answer was too vague.",
    "weak_topics": ["depth", "examples"],
    "needs_probe": True,
}

PROBE_RESULT = {
    "probe_question": "Can you give a specific example of a trade-off you made?",
    "targets": "lack of concrete examples",
}

LONG_ANSWER = "At my previous role I reduced latency from 2 seconds to 200ms by optimizing the database query pipeline and adding caching."


async def test_submit_answer_success(client, test_question, test_session):
    with patch("agents.evaluator.call_groq_eval", return_value=GOOD_EVAL):
        response = await client.post(
            "/api/submit-answer",
            json={
                "session_id": str(test_session.id),
                "question_id": str(test_question.id),
                "answer_text": LONG_ANSWER,
                "is_probe": False,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "answer_id" in data
    assert data["evaluation"]["overall_score"] == 7
    assert data["probe"] is None


async def test_submit_answer_triggers_probe(client, test_question, test_session):
    with patch("agents.evaluator.call_groq_eval", return_value=WEAK_EVAL), \
         patch("graph.nodes.generate_probe", return_value=PROBE_RESULT):
        response = await client.post(
            "/api/submit-answer",
            json={
                "session_id": str(test_session.id),
                "question_id": str(test_question.id),
                "answer_text": LONG_ANSWER,
                "is_probe": False,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["probe"] is not None
    assert "probe_question" in data["probe"]


async def test_probe_circuit_breaker(client, test_question, test_session):
    with patch("agents.evaluator.call_groq_eval", return_value=WEAK_EVAL):
        response = await client.post(
            "/api/submit-answer",
            json={
                "session_id": str(test_session.id),
                "question_id": str(test_question.id),
                "answer_text": LONG_ANSWER,
                "is_probe": True,  # circuit breaker
            },
        )

    assert response.status_code == 200
    assert response.json()["probe"] is None


async def test_submit_answer_too_short(client, test_question, test_session):
    response = await client.post(
        "/api/submit-answer",
        json={
            "session_id": str(test_session.id),
            "question_id": str(test_question.id),
            "answer_text": "short",
            "is_probe": False,
        },
    )
    assert response.status_code == 400


async def test_submit_answer_invalid_session(client, test_question):
    with patch("agents.evaluator.call_groq_eval", return_value=GOOD_EVAL):
        response = await client.post(
            "/api/submit-answer",
            json={
                "session_id": str(uuid.uuid4()),
                "question_id": str(test_question.id),
                "answer_text": LONG_ANSWER,
                "is_probe": False,
            },
        )
    assert response.status_code == 404


async def test_submit_answer_invalid_question(client, test_session):
    with patch("agents.evaluator.call_groq_eval", return_value=GOOD_EVAL):
        response = await client.post(
            "/api/submit-answer",
            json={
                "session_id": str(test_session.id),
                "question_id": str(uuid.uuid4()),
                "answer_text": LONG_ANSWER,
                "is_probe": False,
            },
        )
    assert response.status_code == 404


async def test_answer_persisted_with_evaluation(client, test_question, test_session, db):
    with patch("agents.evaluator.call_groq_eval", return_value=GOOD_EVAL):
        response = await client.post(
            "/api/submit-answer",
            json={
                "session_id": str(test_session.id),
                "question_id": str(test_question.id),
                "answer_text": LONG_ANSWER,
                "is_probe": False,
            },
        )

    answer_id = response.json()["answer_id"]
    result = await db.execute(select(Answer).where(Answer.id == uuid.UUID(answer_id)))
    answer = result.scalar_one_or_none()

    assert answer is not None
    assert answer.score == 7
    assert answer.feedback is not None
    assert answer.weak_topics == []


async def test_get_session_answers(client, test_answer, test_session):
    response = await client.get(f"/api/answers/{test_session.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_answers"] == 1
    assert data["answers"][0]["score"] == 7


async def test_fallback_to_gemini_when_groq_fails(client, test_question, test_session):
    with patch("agents.evaluator.call_groq_eval", side_effect=Exception("Groq down")), \
         patch("agents.evaluator.call_gemini_eval_fallback", return_value=GOOD_EVAL) as mock_gemini:
        response = await client.post(
            "/api/submit-answer",
            json={
                "session_id": str(test_session.id),
                "question_id": str(test_question.id),
                "answer_text": LONG_ANSWER,
                "is_probe": False,
            },
        )

    assert response.status_code == 200
    mock_gemini.assert_called_once()
