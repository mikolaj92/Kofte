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
    assert "american_english" in ids


def test_dispatch_language_only_does_not_need_a_pack():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(text="This is wrong. Fix it.", language="en", style=None)
        ]
    )
    out = dispatch(
        "translate",
        {"text": "To jest źle. Popraw to.", "source": "pl", "target": "en"},
        llm=llm,
    )
    assert out["text"] == "This is wrong. Fix it."
    assert out["language_changed"] is True
    assert out["style_changed"] is False
    assert out["source"] == "pl"
    assert out["target"] == "en"


def test_dispatch_adhoc_form_without_a_pack():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="parser.py still drops empty tags. Re-run the fixture.",
                language="en",
                style=None,
            )
        ]
    )
    out = dispatch(
        "translate",
        {
            "text": "This is wrong. Fix it.",
            "source": "en",
            "target": "en",
            "target_form": "Brief reviewer. Dry. Two sentences. Name the file.",
        },
        llm=llm,
    )
    system = llm.calls[0].messages[0]["content"]
    assert "Brief reviewer" in system
    assert "Name the file" in system
    assert out["language_changed"] is False
