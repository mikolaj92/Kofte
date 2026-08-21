"""Public translate() API: language and style are independent, LLM is injected."""

from __future__ import annotations

import pytest

from kofte import translate
from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft, Turn
from kofte.registers import Register


def test_style_only_english_to_norwegian_jante(mock_llm: MockLLMClient):
    result = translate(
        "This is wrong. Fix it.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        llm=mock_llm,
    )
    assert result.text
    assert result.source.language == "en"
    assert result.target.language == "en"
    assert result.target.style == "norwegian_jante"
    assert result.language_changed is False
    assert result.style_changed is True
    assert mock_llm.calls, "LLM must be invoked"
    system = mock_llm.calls[0].messages[0]["content"].lower()
    assert "keep the language" in system or "same language" in system


def test_polish_to_norwegian_changes_both_axes():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Vi kan se på dette sammen. Noe her fungerer ikke ennå.",
                language="nb",
                style="norwegian_jante",
                moves=["we instead of you", "softened the verdict"],
                preserved=["does not work"],
            )
        ]
    )
    result = translate(
        "To jest źle. Popraw to natychmiast.",
        source="pl+polish_direct",
        target="nb+norwegian_jante",
        llm=llm,
    )
    assert result.target.language == "nb"
    assert result.language_changed is True
    assert result.style_changed is True
    assert "fungerer ikke" in result.text


def test_english_language_norwegian_style_from_polish():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="We might look at this again. Something here is not working yet.",
                language="en",
                style="norwegian_jante",
                moves=["we", "yet"],
                preserved=["not working"],
            )
        ]
    )
    result = translate(
        "To jest źle. Popraw to.",
        source="pl+polish_direct",
        target="en+norwegian_jante",
        llm=llm,
    )
    assert result.target.language == "en"
    assert result.target.style == "norwegian_jante"
    assert result.language_changed is True
    assert result.style_changed is True


def test_context_turns_are_forwarded_to_the_llm():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Happy to take another look together.",
                language="en",
                style="norwegian_jante",
                moves=["we"],
                preserved=["look"],
            )
        ]
    )
    result = translate(
        "This PR is a mess. Do it again.",
        source=Register(language="en", style="polish_direct"),
        target=Register(language="en", style="norwegian_jante"),
        context=[
            Turn(role="user", text="Could you review my pull request?"),
            Turn(role="assistant", text="Sure."),
        ],
        llm=llm,
    )
    blob = "\n".join(m["content"] for m in llm.calls[0].messages)
    assert "review my pull request" in blob
    assert result.text.startswith("Happy")


def test_missing_llm_raises_clear_error():
    with pytest.raises(RuntimeError, match="llm"):
        translate(
            "This is wrong.",
            source="en+polish_direct",
            target="en+norwegian_jante",
        )


def test_result_exposes_moves_and_preserved_facts(mock_llm: MockLLMClient):
    result = translate(
        "This is wrong. The test fails on line 12.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        llm=mock_llm,
    )
    assert result.moves
    assert result.preserved
