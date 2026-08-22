"""Kofte is Norwegian. Compose hops in one pass so facts do not play telephone."""

from __future__ import annotations

from kofte import TranslationDraft, Translator, translate
from kofte.llm import MockLLMClient
from kofte.profiles import bundled_profile
from kofte.registry import ProfileRegistry
from kofte.tools import dispatch


def test_kofte_is_the_norwegian_voice():
    registry = ProfileRegistry.bundled()
    assert "kofte" in registry
    profile = registry.get("kofte")
    assert profile.id == "norwegian_jante"
    assert "kofte" in profile.aliases
    assert bundled_profile("norwegian_jante").aliases == ("kofte",)


def test_en_plus_kofte_is_english_words_norwegian_form():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Something here does not work yet.",
                language="en",
                style="kofte",
            )
        ]
    )
    result = translate(
        "This is wrong. Fix it.",
        source="en",
        target="en+kofte",
        llm=llm,
    )
    assert result.target.style == "kofte"
    assert result.language_changed is False
    assert result.style_changed is True
    system = llm.calls[0].messages[0]["content"].lower()
    assert "jante" in system or "egalitar" in system


def test_hops_are_one_pass_not_telephone():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Something here does not work yet. We could look at it again.",
                language="en",
                style="kofte",
            )
        ]
    )
    result = translate(
        "To jest źle. Popraw to.",
        hops=["pl", "en", "en+kofte"],
        llm=llm,
    )
    assert len(llm.calls) == 1
    user = llm.calls[0].messages[-1]["content"].lower()
    system = llm.calls[0].messages[0]["content"].lower()
    assert "to jest źle" in user
    assert "this is wrong. fix it." not in user
    assert "one pass" in system or "do not write an intermediate" in system
    assert "english" in system
    assert "jante" in system or "kofte" in system or "egalitar" in system
    assert result.text.startswith("Something here")
    assert result.source.language == "pl"
    assert result.target.language == "en"
    assert result.target.style == "kofte"
    assert result.language_changed is True
    assert result.style_changed is True
    assert result.original == "To jest źle. Popraw to."


def test_engine_hops_from_source_are_one_call():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Something here does not work yet.",
                language="en",
                style="kofte",
            )
        ]
    )
    engine = Translator(llm=llm)
    result = engine.translate("To jest źle.", source="pl", hops=["en", "en+kofte"])
    assert len(llm.calls) == 1
    assert "to jest źle" in llm.calls[0].messages[-1]["content"].lower()
    assert result.target.style == "kofte"
    assert result.text == "Something here does not work yet."


def test_dispatch_hops_polish_then_kofte_one_call():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(text="We look again.", language="en", style="kofte"),
        ]
    )
    out = dispatch(
        "translate",
        {"text": "To jest źle.", "hops": ["pl", "en", "en+kofte"]},
        llm=llm,
    )
    assert len(llm.calls) == 1
    assert out["text"] == "We look again."
    assert out["source"] == "pl"
    assert out["target"] == "en+kofte"
    assert out["language_changed"] is True
    assert out["style_changed"] is True
