"""OpenAI-style tool schema + dispatch, so any model can call Kofte without MCP."""

from __future__ import annotations

from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft
from kofte.tools import TOOLS, dispatch


def test_tools_include_translate_and_list_profiles():
    names = {t["function"]["name"] for t in TOOLS}
    assert "translate" in names
    assert "list_profiles" in names
    assert "describe_profile" in names


def test_dispatch_translate():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="We can look again.",
                language="en",
                style="norwegian_jante",
            )
        ]
    )
    out = dispatch(
        "translate",
        {
            "text": "This is wrong.",
            "source": "en+polish_direct",
            "target": "en+norwegian_jante",
        },
        llm=llm,
    )
    assert out["text"] == "We can look again."
    assert out["style_changed"] is True


def test_dispatch_list_profiles():
    out = dispatch("list_profiles", {})
    ids = {p["id"] for p in out["profiles"]}
    assert "norwegian_jante" in ids
