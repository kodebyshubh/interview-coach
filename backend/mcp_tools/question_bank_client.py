"""Sync wrapper around a real MCP client session for the question bank server.

The rest of the backend (graph/nodes.py) is synchronous, but the MCP SDK's
ClientSession is async-native, so each call here spins up one short-lived
event loop, spawns the server as a stdio subprocess, does the MCP handshake
(initialize -> list_tools / call_tool), and tears it down. Mirrors the
single-purpose-function shape of rag/retriever.py — one thing per function,
no connection pooling or long-lived session management, since this tool is
called at most once per generated question.
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=[str(Path(__file__).parent / "question_bank_server.py")],
)


async def _list_tools_async() -> list[dict]:
    async with stdio_client(_SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema,
                    },
                }
                for t in result.tools
            ]


async def _call_tool_async(name: str, arguments: dict) -> dict:
    async with stdio_client(_SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            if result.isError:
                raise RuntimeError(f"MCP tool {name!r} failed: {result.content}")
            # FastMCP returns a single text content block containing JSON for dict returns
            return json.loads(result.content[0].text)


def list_bank_tools_openai_format() -> list[dict]:
    """The question-bank server's tools, translated into OpenAI/Groq-style `tools=` schema."""
    return asyncio.run(_list_tools_async())


def call_get_bank_question(role: str, question_type: str) -> dict:
    """Direct MCP protocol call to get_bank_question — no LLM involved. Used as the
    last-resort fallback when the LLM-mediated path (see graph/nodes.py) can't run
    because there's no live LLM left to make the tool-call decision."""
    return asyncio.run(_call_tool_async("get_bank_question", {
        "role": role,
        "question_type": question_type,
    }))
