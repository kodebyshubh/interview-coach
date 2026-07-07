import json
from types import SimpleNamespace
from unittest.mock import patch

from graph.nodes import _generate_with_bank_tool

FAKE_TOOLS = [{
    "type": "function",
    "function": {"name": "get_bank_question", "description": "...", "parameters": {}},
}]

BANK_QUESTION = {
    "question": "Tell me about a time you debugged a production issue.",
    "expected_themes": ["debugging", "incident response"],
    "difficulty": "medium",
    "question_type": "behavioral",
}


def _groq_response_with_tool_call(role: str, question_type: str):
    tool_call = SimpleNamespace(
        function=SimpleNamespace(
            name="get_bank_question",
            arguments=json.dumps({"role": role, "question_type": question_type}),
        )
    )
    message = SimpleNamespace(tool_calls=[tool_call], content=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _groq_response_plain(question_type: str):
    content = json.dumps({
        "question": "Freshly generated question.",
        "expected_themes": ["a", "b"],
        "difficulty": "medium",
        "question_type": question_type,
    })
    message = SimpleNamespace(tool_calls=None, content=content)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_llm_chooses_bank_tool():
    with patch("graph.nodes.list_bank_tools_openai_format", return_value=FAKE_TOOLS), \
         patch("graph.nodes.groq_client") as mock_groq_client, \
         patch("graph.nodes.call_get_bank_question", return_value=dict(BANK_QUESTION)) as mock_call_tool:
        mock_groq_client.chat.completions.create.return_value = _groq_response_with_tool_call(
            "Backend Engineer", "behavioral"
        )
        result = _generate_with_bank_tool("resume ctx", "jd ctx", "behavioral", "Backend Engineer")

    mock_call_tool.assert_called_once_with("Backend Engineer", "behavioral")
    assert result["source"] == "mcp_bank"
    assert result["question"] == BANK_QUESTION["question"]

    # tools were actually bound on the Groq call — this is the real assertion that
    # matters: it proves a real tool binding reached the LLM SDK call, not just that
    # our own code branched on a hardcoded condition.
    _, call_kwargs = mock_groq_client.chat.completions.create.call_args
    assert call_kwargs["tools"] == FAKE_TOOLS
    assert call_kwargs["tool_choice"] == "auto"


def test_llm_writes_fresh_question_instead():
    with patch("graph.nodes.list_bank_tools_openai_format", return_value=FAKE_TOOLS), \
         patch("graph.nodes.groq_client") as mock_groq_client, \
         patch("graph.nodes.call_get_bank_question") as mock_call_tool:
        mock_groq_client.chat.completions.create.return_value = _groq_response_plain("technical")
        result = _generate_with_bank_tool("resume ctx", "jd ctx", "technical", "Backend Engineer")

    mock_call_tool.assert_not_called()
    assert result["source"] == "groq"
    assert result["question"] == "Freshly generated question."
