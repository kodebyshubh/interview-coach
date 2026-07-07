from unittest.mock import patch

import pytest

from agents.probe_generator import generate_probe

ORIGINAL_Q = "Tell me about a time you reduced latency."
ANSWER = "I worked on some projects involving performance improvements."
WEAK_TOPICS = ["concrete examples", "metrics"]
FEEDBACK = "Answer lacks specific examples and quantitative results."

PROBE_RESULT = {
    "probe_question": "Can you give a specific metric from that optimization?",
    "targets": "lack of quantitative evidence",
}


def test_generate_probe_returns_correct_shape():
    with patch("agents.probe_generator._call_gemini_probe", return_value=PROBE_RESULT):
        result = generate_probe(ORIGINAL_Q, ANSWER, WEAK_TOPICS, FEEDBACK)

    assert "probe_question" in result
    assert "targets" in result


def test_gemini_primary_for_probe():
    with patch("agents.probe_generator._call_gemini_probe", return_value=PROBE_RESULT) as mock_gemini:
        generate_probe(ORIGINAL_Q, ANSWER, WEAK_TOPICS, FEEDBACK)
    mock_gemini.assert_called_once()


def test_groq_fallback_for_probe():
    with patch("agents.probe_generator._call_gemini_probe", side_effect=Exception("Gemini down")), \
         patch("agents.probe_generator._call_groq_probe", return_value=PROBE_RESULT) as mock_groq:
        result = generate_probe(ORIGINAL_Q, ANSWER, WEAK_TOPICS, FEEDBACK)

    mock_groq.assert_called_once()
    assert result["probe_question"] is not None


def test_probe_prompt_includes_weak_topics():
    with patch("agents.probe_generator._call_gemini_probe", return_value=PROBE_RESULT) as mock_gemini:
        generate_probe(ORIGINAL_Q, ANSWER, WEAK_TOPICS, FEEDBACK)

    prompt_arg = mock_gemini.call_args[0][0]
    for topic in WEAK_TOPICS:
        assert topic in prompt_arg


def test_probe_with_empty_weak_topics():
    with patch("agents.probe_generator._call_gemini_probe", return_value=PROBE_RESULT) as mock_gemini:
        result = generate_probe(ORIGINAL_Q, ANSWER, [], FEEDBACK)

    prompt_arg = mock_gemini.call_args[0][0]
    assert "general weakness" in prompt_arg
    assert result is not None
