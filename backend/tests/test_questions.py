import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select

from db.models import Question


def _make_question_return(question_type: str) -> dict:
    return {
        "question": f"Sample {question_type} question.",
        "expected_themes": ["theme1", "theme2"],
        "difficulty": "medium",
        "question_type": question_type,
    }


def _gemini_side_effects():
    order = (
        ["behavioral"] * 3 + ["technical"] * 3 + ["situational"] * 1 + ["resume_deep_dive"] * 1
    )
    return [_make_question_return(qt) for qt in order]


@pytest.fixture
def mock_generation():
    # Tool-aware generation (graph.nodes._generate_with_bank_tool) is tier 1 and is
    # covered by its own dedicated tests — disable it here so these route-level tests
    # exercise the standard Gemini/Groq path (tier 2) they were written against.
    with patch("graph.nodes._generate_with_bank_tool", side_effect=Exception("disabled for this test")), \
         patch("agents.question_generator.call_gemini") as mock_gemini, \
         patch("agents.question_generator.retrieve_resume_context", return_value=["ctx"]), \
         patch("agents.question_generator.retrieve_jd_context", return_value=["ctx"]):
        mock_gemini.side_effect = _gemini_side_effects()
        yield mock_gemini


async def test_generate_questions_success(client, test_session, mock_generation):
    response = await client.post(
        "/api/generate-questions",
        json={"session_id": str(test_session.id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["questions_generated"] == 8
    assert len(data["questions"]) == 8


async def test_generate_questions_invalid_session(client):
    response = await client.post(
        "/api/generate-questions",
        json={"session_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


async def test_generate_questions_duplicate_call(client, test_session, mock_generation):
    await client.post("/api/generate-questions", json={"session_id": str(test_session.id)})

    mock_generation.side_effect = _gemini_side_effects()
    response = await client.post(
        "/api/generate-questions",
        json={"session_id": str(test_session.id)},
    )
    assert response.status_code == 400


async def test_generated_questions_persisted_in_db(client, test_session, db, mock_generation):
    await client.post("/api/generate-questions", json={"session_id": str(test_session.id)})

    result = await db.execute(
        select(Question).where(Question.session_id == test_session.id)
    )
    questions = result.scalars().all()
    assert len(questions) == 8


async def test_get_questions_by_session(client, test_session, mock_generation):
    await client.post("/api/generate-questions", json={"session_id": str(test_session.id)})

    response = await client.get(f"/api/questions/{test_session.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 8


async def test_get_questions_wrong_session(client):
    response = await client.get(f"/api/questions/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_question_types_distribution(client, test_session, mock_generation):
    await client.post("/api/generate-questions", json={"session_id": str(test_session.id)})

    response = await client.get(f"/api/questions/{test_session.id}")
    questions = response.json()["questions"]

    types = [q["question_type"] for q in questions]
    assert types.count("behavioral") == 3
    assert types.count("technical") == 3
    assert types.count("situational") == 1
    assert types.count("resume_deep_dive") == 1
