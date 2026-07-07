from unittest.mock import patch

from graph.build import graph


def _make_q(question_type: str) -> dict:
    return {
        "question": f"Sample {question_type} question.",
        "expected_themes": ["theme1"],
        "difficulty": "medium",
        "question_type": question_type,
    }


def _all_side_effects():
    from agents.question_generator import get_question_plan
    return [_make_q(qt) for qt in get_question_plan()]


def _initial_state(session_id="test-session-123", role="Backend Engineer"):
    from agents.question_generator import get_question_plan

    return {
        "stage": "generate_questions",
        "session_id": session_id,
        "role": role,
        "resume_context": "resume ctx",
        "jd_context": "jd ctx",
        "question_plan": get_question_plan(),
        "questions": [],
    }


def test_generate_questions_returns_8():
    with patch("graph.nodes._generate_with_bank_tool", side_effect=Exception("disabled for this test")), \
         patch("agents.question_generator.call_gemini") as mock_gemini:
        mock_gemini.side_effect = _all_side_effects()
        result = graph.invoke(_initial_state())
    assert len(result["questions"]) == 8


def test_question_mix_correct():
    with patch("graph.nodes._generate_with_bank_tool", side_effect=Exception("disabled for this test")), \
         patch("agents.question_generator.call_gemini") as mock_gemini:
        mock_gemini.side_effect = _all_side_effects()
        result = graph.invoke(_initial_state())

    types = [q["question_type"] for q in result["questions"]]
    assert types.count("behavioral") == 3
    assert types.count("technical") == 3
    assert types.count("situational") == 1
    assert types.count("resume_deep_dive") == 1


def test_gemini_primary_called_once_per_question():
    with patch("graph.nodes._generate_with_bank_tool", side_effect=Exception("disabled for this test")), \
         patch("agents.question_generator.call_gemini") as mock_gemini:
        mock_gemini.side_effect = _all_side_effects()
        graph.invoke(_initial_state())
    assert mock_gemini.call_count == 8


def test_groq_fallback_on_gemini_failure():
    groq_result = _make_q("behavioral")
    groq_result["source"] = "groq"

    with patch("graph.nodes._generate_with_bank_tool", side_effect=Exception("disabled for this test")), \
         patch("agents.question_generator.call_gemini", side_effect=Exception("Gemini down")), \
         patch("agents.question_generator.call_groq_fallback", return_value=groq_result) as mock_groq:
        result = graph.invoke(_initial_state())

    assert mock_groq.call_count == 8
    assert all(q["source"] == "groq" for q in result["questions"])


def test_output_contains_required_keys():
    with patch("graph.nodes._generate_with_bank_tool", side_effect=Exception("disabled for this test")), \
         patch("agents.question_generator.call_gemini") as mock_gemini:
        mock_gemini.side_effect = _all_side_effects()
        result = graph.invoke(_initial_state())

    for q in result["questions"]:
        assert "question" in q
        assert "expected_themes" in q
        assert "difficulty" in q
        assert "question_type" in q


def test_session_id_attached_to_each_question():
    with patch("graph.nodes._generate_with_bank_tool", side_effect=Exception("disabled for this test")), \
         patch("agents.question_generator.call_gemini") as mock_gemini:
        mock_gemini.side_effect = _all_side_effects()
        result = graph.invoke(_initial_state(session_id="test-session-123"))

    assert all(q["session_id"] == "test-session-123" for q in result["questions"])
