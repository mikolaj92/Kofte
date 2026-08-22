"""Hops are outputs. Source is optional. One hop: the LLM infers the input."""

from __future__ import annotations

import pytest

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


def test_single_hop_infers_source_from_the_message():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Something here does not work yet. We could look at it again.",
                language="en",
                style="kofte",
            )
        ]
    )
    result = translate("To jest źle. Popraw to.", hops=["en+kofte"], llm=llm)
    assert len(llm.calls) == 1
    user = llm.calls[0].messages[-1]["content"].lower()
    system = llm.calls[0].messages[0]["content"].lower()
    assert "to jest źle" in user
    assert "detect" in system or "infer" in system
    assert "english" in system
    assert "jante" in system or "kofte" in system or "egalitar" in system
    assert "polish" not in system or "detect" in system
    assert result.target.language == "en"
    assert result.target.style == "kofte"
    assert result.source.language is None
    assert result.original == "To jest źle. Popraw to."


def test_hops_are_outputs_source_stays_optional():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Something here does not work yet.",
                language="en",
                style="kofte",
            )
        ]
    )
    result = translate("To jest źle.", hops=["en", "en+kofte"], llm=llm)
    assert len(llm.calls) == 1
    system = llm.calls[0].messages[0]["content"].lower()
    user = llm.calls[0].messages[-1]["content"].lower()
    assert "to jest źle" in user
    assert "detect" in system or "infer" in system
    assert "outputs" in system or "en+kofte" in system or "kofte" in system
    assert result.source.language is None
    assert result.target.style == "kofte"


def test_explicit_source_still_pins_when_given():
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
        "To jest źle.",
        source="pl",
        hops=["en+kofte"],
        llm=llm,
    )
    system = llm.calls[0].messages[0]["content"].lower()
    assert "polish" in system
    assert result.source.language == "pl"
    assert result.target.style == "kofte"
    assert result.language_changed is True


def test_zero_hops_without_source_and_target_is_an_error():
    llm = MockLLMClient(responses=[])
    with pytest.raises(ValueError, match="hops|target"):
        translate("To jest źle.", hops=[], llm=llm)
    with pytest.raises(ValueError, match="hops|target"):
        translate("To jest źle.", llm=llm)


def test_engine_single_hop_from_source_kwarg():
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
    result = engine.translate("To jest źle.", hops=["en+kofte"])
    assert len(llm.calls) == 1
    assert "to jest źle" in llm.calls[0].messages[-1]["content"].lower()
    assert result.target.style == "kofte"


def test_dispatch_single_hop_infers_source():
    llm = MockLLMClient(
        responses=[TranslationDraft(text="We look again.", language="en", style="kofte")]
    )
    out = dispatch(
        "translate",
        {"text": "To jest źle.", "hops": ["en+kofte"]},
        llm=llm,
    )
    assert len(llm.calls) == 1
    assert out["text"] == "We look again."
    assert out["target"] == "en+kofte"
    assert out["source"] == "auto"


def test_style_only_hop_keeps_detected_language():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Tu jeszcze coś nie działa. Możemy spojrzeć razem.",
                language="pl",
                style="kofte",
            )
        ]
    )
    result = translate("To jest źle. Popraw to.", hops=["kofte"], llm=llm)
    system = llm.calls[0].messages[0]["content"].lower()
    assert "detect" in system or "infer" in system
    assert result.target.style == "kofte"
    assert result.source.language is None
