"""MCP tools: list_profiles, describe_profile, translate. Model-callable."""

from __future__ import annotations

import pytest

from kofte.llm import MockLLMClient
from kofte.mcp_server import create_server
from kofte.models import TranslationDraft


@pytest.mark.asyncio
async def test_mcp_lists_bundled_profiles():
    server = create_server(llm=MockLLMClient(responses=[]))
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert {"list_profiles", "describe_profile", "translate"} <= names
    result = await server.call_tool("list_profiles", {})
    payload = _payload(result)
    ids = {item["id"] for item in payload["profiles"]}
    assert "norwegian_jante" in ids
    assert "polish_direct" in ids
    assert "american_english" in ids


@pytest.mark.asyncio
async def test_mcp_describe_profile_returns_rules():
    server = create_server(llm=MockLLMClient(responses=[]))
    result = await server.call_tool("describe_profile", {"profile_id": "norwegian_jante"})
    payload = _payload(result)
    assert payload["id"] == "norwegian_jante"
    assert "janteloven" in payload["supreme"]
    assert any("facts" in r.lower() or "we" in r.lower() for r in payload["rules"])


@pytest.mark.asyncio
async def test_mcp_translate_style_only():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Something here does not work yet.",
                language="en",
                style="norwegian_jante",
                moves=["softened"],
                preserved=["does not work"],
            )
        ]
    )
    server = create_server(llm=llm)
    result = await server.call_tool(
        "translate",
        {
            "text": "This is wrong. Fix it.",
            "source": "en+polish_direct",
            "target": "en+norwegian_jante",
        },
    )
    payload = _payload(result)
    assert payload["text"] == "Something here does not work yet."
    assert payload["language_changed"] is False
    assert payload["style_changed"] is True


def _payload(result):
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "content"):
        import json

        for block in result.content:
            text = getattr(block, "text", None)
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"text": text}
    if isinstance(result, dict):
        return result
    raise AssertionError(f"unreadable MCP result: {result!r}")


@pytest.mark.asyncio
async def test_mcp_translate_language_only():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(text="This is wrong. Fix it.", language="en", style=None)
        ]
    )
    server = create_server(llm=llm)
    result = await server.call_tool(
        "translate",
        {"text": "To jest źle. Popraw to.", "source": "pl", "target": "en"},
    )
    payload = _payload(result)
    assert payload["text"] == "This is wrong. Fix it."
    assert payload["language_changed"] is True
    assert payload["style_changed"] is False


@pytest.mark.asyncio
async def test_mcp_translate_adhoc_form():
    llm = MockLLMClient(
        responses=[TranslationDraft(text="ok", language="en", style=None)]
    )
    server = create_server(llm=llm)
    result = await server.call_tool(
        "translate",
        {
            "text": "This is wrong. Fix it.",
            "source": "en",
            "target": "en",
            "target_form": "Brief reviewer. Name the file.",
        },
    )
    payload = _payload(result)
    assert payload["text"] == "ok"
    system = llm.calls[0].messages[0]["content"]
    assert "Brief reviewer" in system
