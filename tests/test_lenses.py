"""A Lens is anything that can describe how to rewrite a message.

Style folders and host-built trait lists are two sources of the same engine.
"""

from __future__ import annotations

from kofte import AdHocLens, TranslationDraft, Translator, translate
from kofte.lenses import lens_from_traits
from kofte.llm import MockLLMClient
from kofte.profiles import bundled_profile
from kofte.prompts import build_messages
from kofte.registers import Register


def test_adhoc_lens_is_enough_without_a_folder():
    reviewer = AdHocLens(
        id="brief_reviewer",
        name="Brief reviewer",
        summary="Short notes. Name the file and the next step.",
        lines=(
            "Tone: dry",
            "Length: two sentences",
            "Always name the file",
        ),
    )
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="parser.py still drops empty tags. Re-run the fixture.",
                language="en",
                style="brief_reviewer",
            )
        ]
    )
    result = translate(
        "This is wrong. Fix it.",
        source="en",
        target="en",
        target_lens=reviewer,
        llm=llm,
    )
    blob = "\n".join(m["content"] for m in llm.calls[0].messages)
    assert "Brief reviewer" in blob
    assert "Always name the file" in blob
    assert result.target.language == "en"
    assert result.style_changed is False


def test_source_and_target_lenses_both_land_in_the_prompt():
    speaker = lens_from_traits(
        "legal_caution",
        "Legal caution",
        [("Register", "hedged"), ("Risk", "name the liability")],
        summary="Do not overclaim.",
    )
    listener = lens_from_traits(
        "brief_reviewer",
        "Brief reviewer",
        [("Tone", "dry"), ("Length", "two sentences")],
        summary="Short notes.",
    )
    messages = build_messages(
        text="This is wrong. Fix it.",
        source=Register(language="en"),
        target=Register(language="en"),
        source_lens=speaker,
        target_lens=listener,
    )
    joined = "\n".join(m["content"] for m in messages)
    assert "Legal caution" in joined
    assert "Brief reviewer" in joined
    assert "keep the language" in joined.lower() or "same language" in joined.lower()


def test_style_profile_is_a_lens():
    profile = bundled_profile("norwegian_jante")
    block = profile.prompt_block("Target")
    assert "norwegian_jante" in block
    assert "Janteloven" in block or "jante" in block.lower()


def test_american_english_profile_is_a_lens():
    profile = bundled_profile("american_english")
    block = profile.prompt_block("Target")
    assert "american_english" in block
    assert "agency" in block.lower() or "I" in block


def test_engine_accepts_lens_not_in_registry():
    llm = MockLLMClient(
        responses=[TranslationDraft(text="ok", language="en", style=None)]
    )
    engine = Translator(llm=llm)
    lens = AdHocLens(id="custom", name="Custom", summary="Be brief.", lines=("short sentences",))
    result = engine.translate(
        "Please consider potentially maybe fixing this.",
        source="en",
        target="en",
        target_lens=lens,
    )
    assert "Be brief" in llm.calls[0].messages[0]["content"]
    assert result.text == "ok"


def test_explicit_lens_wins_over_register_style():
    llm = MockLLMClient(
        responses=[TranslationDraft(text="ok", language="en", style="norwegian_jante")]
    )
    engine = Translator(llm=llm)
    lens = AdHocLens(
        id="brief_reviewer",
        name="Brief reviewer",
        summary="Short notes.",
        lines=("two sentences",),
    )
    engine.translate(
        "Fix it.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        target_lens=lens,
    )
    system = llm.calls[0].messages[0]["content"]
    assert "Brief reviewer" in system
    assert "two sentences" in system
