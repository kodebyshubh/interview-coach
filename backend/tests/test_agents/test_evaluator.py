from unittest.mock import patch

import pytest

from agents.evaluator import evaluate_answer

Q_TEXT = "Tell me about a time you reduced latency."
Q_TYPE = "behavioral"
THEMES = ["optimization", "async"]
ANSWER = "At Tez Health I built a real-time STT pipeline. I reduced time-to-first-audio from 4s to 400ms."

GOOD_EVAL = {
    "scores": {"clarity": 8, "depth": 7, "relevance": 9, "examples": 8},
    "overall_score": 8,
    "feedback": "Strong with concrete metrics.",
    "weak_topics": [],
    "needs_probe": False,
}

WEAK_EVAL = {
    "scores": {"clarity": 4, "depth": 3, "relevance": 5, "examples": 2},
    "overall_score": 4,
    "feedback": "Too vague.",
    "weak_topics": ["depth"],
    "needs_probe": True,
}


def test_evaluate_answer_returns_correct_shape():
    with patch("agents.evaluator.call_groq_eval", return_value=GOOD_EVAL):
        result = evaluate_answer(Q_TEXT, Q_TYPE, THEMES, ANSWER)

    assert "scores" in result
    assert set(result["scores"].keys()) == {"clarity", "depth", "relevance", "examples"}
    assert "overall_score" in result
    assert "feedback" in result
    assert "weak_topics" in result
    assert "needs_probe" in result


def test_evaluate_answer_groq_primary():
    with patch("agents.evaluator.call_groq_eval", return_value=GOOD_EVAL) as mock_groq:
        evaluate_answer(Q_TEXT, Q_TYPE, THEMES, ANSWER)
    mock_groq.assert_called_once()


def test_evaluate_answer_falls_back_to_gemini():
    with patch("agents.evaluator.call_groq_eval", side_effect=Exception("timeout")), \
         patch("agents.evaluator.call_gemini_eval_fallback", return_value=GOOD_EVAL) as mock_gemini:
        result = evaluate_answer(Q_TEXT, Q_TYPE, THEMES, ANSWER)

    mock_gemini.assert_called_once()
    assert result["overall_score"] == 8


def test_evaluate_answer_falls_back_to_ollama_when_both_fail():
    with patch("agents.evaluator.call_groq_eval", side_effect=Exception("groq down")), \
         patch("agents.evaluator.call_gemini_eval_fallback", side_effect=Exception("gemini down")), \
         patch("agents.evaluator.call_ollama_eval", return_value=GOOD_EVAL) as mock_ollama:
        result = evaluate_answer(Q_TEXT, Q_TYPE, THEMES, ANSWER)

    mock_ollama.assert_called_once()
    assert result["overall_score"] == 8
    assert result["source"] == "ollama"


def test_needs_probe_true_when_score_below_6():
    with patch("agents.evaluator.call_groq_eval", return_value=WEAK_EVAL):
        result = evaluate_answer(Q_TEXT, Q_TYPE, THEMES, ANSWER)
    assert result["needs_probe"] is True


def test_needs_probe_false_when_score_above_6():
    with patch("agents.evaluator.call_groq_eval", return_value=GOOD_EVAL):
        result = evaluate_answer(Q_TEXT, Q_TYPE, THEMES, ANSWER)
    assert result["needs_probe"] is False


def test_needs_probe_is_computed_not_trusted_at_score_6():
    """The model's own needs_probe field is deliberately wrong here (True) to prove
    Python's override wins — this is what actually closes the boundary bug, not
    prompt wording. overall_score=6 must always yield needs_probe=False."""
    mock_eval = {**GOOD_EVAL, "overall_score": 6, "needs_probe": True}
    with patch("agents.evaluator.call_groq_eval", return_value=mock_eval):
        result = evaluate_answer(Q_TEXT, Q_TYPE, THEMES, ANSWER)
    assert result["overall_score"] == 6
    assert result["needs_probe"] is False


def test_needs_probe_is_computed_not_trusted_at_score_5():
    """Same proof at the other side of the boundary — model says False, code must
    still say True since overall_score=5 < 6."""
    mock_eval = {**WEAK_EVAL, "overall_score": 5, "needs_probe": False}
    with patch("agents.evaluator.call_groq_eval", return_value=mock_eval):
        result = evaluate_answer(Q_TEXT, Q_TYPE, THEMES, ANSWER)
    assert result["overall_score"] == 5
    assert result["needs_probe"] is True


def test_evaluate_answer_rejects_empty_themes():
    with patch("agents.evaluator.call_groq_eval", return_value=GOOD_EVAL) as mock_groq:
        result = evaluate_answer(Q_TEXT, Q_TYPE, [], ANSWER)

    mock_groq.assert_called_once()
    prompt_arg = mock_groq.call_args[0][0]
    assert "None specified" in prompt_arg
    assert result is not None
