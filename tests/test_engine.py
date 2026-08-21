"""Translator is the reusable engine: registry + llm + filters."""

from __future__ import annotations

from pathlib import Path

import pytest

from kofte import TranslationDraft, Translator
from kofte.errors import UnknownProfileError
from kofte.llm import MockLLMClient
from kofte.models import Turn
from kofte.profiles import load_profile


def test_translator_resolves_custom_style_without_passing_profile(tmp_path: Path):
    folder = tmp_path / "quiet_brit"
    folder.mkdir()
    (folder / "profile.toml").write_text(
        """
id = "quiet_brit"
name = "Quiet British"
language_hint = "en"
summary = "Understate."
supreme = ["understatement"]
[[axes]]
id = "understatement"
name = "Understatement"
description = "Say less."
""".lstrip()
    )
    llm = MockLLMClient(
        responses=[
            TranslationDraft(text="Perhaps we revisit this.", language="en", style="quiet_brit")
        ]
    )
    engine = Translator(llm=llm)
    engine.registry.register(load_profile(folder))
    result = engine.translate(
        "This is wrong. Fix it.", source="en+polish_direct", target="en+quiet_brit"
    )
    assert result.target.style == "quiet_brit"
    assert "quiet british" in llm.calls[0].messages[0]["content"].lower()


def test_module_translate_still_works_with_bundled_profiles():
    from kofte import translate

    llm = MockLLMClient(
        responses=[TranslationDraft(text="we look again", language="en", style="norwegian_jante")]
    )
    result = translate(
        "This is wrong.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        llm=llm,
    )
    assert result.style_changed is True


def test_unknown_style_on_engine_is_a_clear_error():
    llm = MockLLMClient(
        responses=[TranslationDraft(text="x", language="en", style="nope")]
    )
    engine = Translator(llm=llm)
    with pytest.raises(UnknownProfileError, match="nope"):
        engine.translate("hi", source="en+polish_direct", target="en+nope")


def test_engine_forwards_context():
    llm = MockLLMClient(
        responses=[TranslationDraft(text="sure", language="en", style="norwegian_jante")]
    )
    engine = Translator(llm=llm)
    engine.translate(
        "Do it again.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        context=[Turn(role="user", text="please review")],
    )
    blob = "\n".join(m["content"] for m in llm.calls[0].messages)
    assert "please review" in blob
