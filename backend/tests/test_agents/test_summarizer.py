from unittest.mock import patch

import pytest

from agents.summarizer import compute_stats, generate_session_summary


def _make_answer(question_type: str, score: int, weak_topics=None) -> dict:
    return {
        "question_text": f"Sample {question_type} question.",
        "question_type": question_type,
        "answer_text": "My answer involved optimizing the query pipeline and reducing latency.",
        "score": score,
        "feedback": "Good answer.",
        "weak_topics": weak_topics or [],
    }


MOCK_SUMMARY_RESULT = {
    "overall_score": 6.7,
    "performance_band": "decent",
    "one_line_verdict": "Solid but needs more depth.",
    "top_strengths": [{"topic": "communication", "evidence": "Clear answers."}],
    "top_weaknesses": [{"topic": "system design", "pattern": "surface level", "action": "Read DDIA"}],
    "question_type_analysis": {"behavioral": "strong", "technical": "needs work"},
    "recommended_resources": [{"title": "DDIA", "type": "concept", "reason": "For depth"}],
}


def test_compute_stats_correct_average():
    answers = [
        _make_answer("behavioral", 6),
        _make_answer("technical", 8),
        _make_answer("behavioral", 7),
    ]
    stats = compute_stats(answers)
    assert stats["avg_score"] == 7.0


def test_compute_stats_type_breakdown():
    answers = [
        _make_answer("behavioral", 6),
        _make_answer("behavioral", 8),
        _make_answer("technical", 4),
    ]
    stats = compute_stats(answers)
    assert stats["type_breakdown"]["behavioral"] == 7.0
    assert stats["type_breakdown"]["technical"] == 4.0


def test_compute_stats_top_weak_topics():
    answers = [
        _make_answer("behavioral", 5, weak_topics=["system design", "depth"]),
        _make_answer("technical", 4, weak_topics=["system design", "caching"]),
        _make_answer("behavioral", 6, weak_topics=["system design"]),
    ]
    stats = compute_stats(answers)
    assert stats["top_weak_topics"][0] == "system design"


def test_generate_session_summary_returns_shape():
    answers = [_make_answer("behavioral", 7) for _ in range(3)]

    with patch("agents.summarizer.call_gemini_summary", return_value=MOCK_SUMMARY_RESULT):
        result = generate_session_summary("Backend Engineer", answers)

    assert "overall_score" in result
    assert "computed_stats" in result


def test_gemini_primary_for_summary():
    answers = [_make_answer("behavioral", 7) for _ in range(3)]

    with patch("agents.summarizer.call_gemini_summary", return_value=MOCK_SUMMARY_RESULT) as mock_gemini:
        generate_session_summary("Backend Engineer", answers)

    mock_gemini.assert_called_once()


def test_groq_fallback_for_summary():
    answers = [_make_answer("behavioral", 7) for _ in range(3)]

    with patch("agents.summarizer.call_gemini_summary", side_effect=Exception("Gemini down")), \
         patch("agents.summarizer.call_groq_summary_fallback", return_value=MOCK_SUMMARY_RESULT) as mock_groq:
        result = generate_session_summary("Backend Engineer", answers)

    mock_groq.assert_called_once()
    assert "overall_score" in result


def test_probe_answers_excluded():
    """generate_session_summary receives pre-filtered answers (route excludes probes).
    Verify the answers_block only reflects what was passed."""
    non_probe_answers = [_make_answer("behavioral", 7) for _ in range(3)]

    with patch("agents.summarizer.call_gemini_summary", return_value=MOCK_SUMMARY_RESULT) as mock_gemini:
        generate_session_summary("Backend Engineer", non_probe_answers)

    prompt = mock_gemini.call_args[0][0]
    assert "Q3" in prompt
    assert "Q4" not in prompt  # only 3 answers passed
