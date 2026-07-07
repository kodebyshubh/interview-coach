"""MCP server exposing a curated, static question bank as a real MCP tool.

Run standalone for manual inspection: `python question_bank_server.py`
Normally launched as a subprocess by question_bank_client.py over stdio.
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

_BANK_PATH = Path(__file__).parent / "question_bank.json"
_BANK = json.loads(_BANK_PATH.read_text())

mcp = FastMCP("question-bank")


@mcp.tool()
def get_bank_question(role: str, question_type: str) -> dict:
    """Fetch a curated, pre-written interview question for a given role and question
    type from the static question bank. Prefer this over generating a new question
    from scratch when a good generic match already exists for a common role/type
    combination — it's free and instant, with no LLM call needed. Not available for
    question_type='resume_deep_dive', since those must reference the specific
    candidate's actual resume content and can't be pre-written generically.
    """
    matches = [
        q for q in _BANK
        if q["question_type"] == question_type
        and role.lower() in [r.lower() for r in q["roles"]]
    ]
    if not matches:
        matches = [q for q in _BANK if q["question_type"] == question_type]
    if not matches:
        raise ValueError(f"No bank question available for question_type={question_type!r}")

    match = matches[0]
    return {
        "question": match["question"],
        "expected_themes": match["expected_themes"],
        "difficulty": match["difficulty"],
        "question_type": match["question_type"],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
