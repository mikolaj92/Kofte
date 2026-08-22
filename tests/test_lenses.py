"""A Lens is anything that can describe how to rewrite a message.

Style folders and EMI trait lists are two sources of the same thing.
Kofte does not own EMI; the host builds a lens from traits.
"""

from __future__ import annotations

from kofte import AdHocLens, TranslationDraft, Translator, translate
from kofte.lenses import lens_from_traits
from kofte.llm import MockLLMClient
from kofte.profiles import bundled_profile
from kofte.prompts import build_messages
from kofte.registers import Register


def test_adhoc_lens_is_enough_for_emi_without_a_folder():
    listener = AdHocLens(
        id="emi:203412107403302401",
        name="Listener",
        summary="Kontraktowiec, level 4.",
        lines=(
            "Osobowość: Kontraktowiec",
            "Faktor: dynamika 4",
            "Stan umysłu: emi3",
        ),
    )
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="We could look at this together.",
                language="pl",
                style="emi:203412107403302401",
            )
        ]
    )
    result = translate(
        "To jest źle. Popraw to.",
        source="pl",
        target="pl",
        target_lens=listener,
        llm=llm,
    )
    blob = "\n".join(m["content"] for m in llm.calls[0].messages)
    assert "Kontraktowiec" in blob
    assert "emi3" in blob
    assert result.target.language == "pl"
    assert result.style_changed is False


def test_speaker_and_listener_lenses_both_land_in_the_prompt():
    speaker = lens_from_traits(
        "emi:speaker",
        "Speaker",
        [("Osobowość", "Sędzia"), ("Stan umysłu", "emi8")],
        summary="Direct, justice-first.",
    )
    listener = lens_from_traits(
        "emi:listener",
        "Listener",
        [("Osobowość", "Kontraktowiec"), ("Stan umysłu", "emi3")],
        summary="Contract, keep it concrete.",
    )
    messages = build_messages(
        text="This is wrong. Fix it.",
        source=Register(language="en"),
        target=Register(language="en"),
        source_lens=speaker,
        target_lens=listener,
    )
    joined = "\n".join(m["content"] for m in messages)
    assert "Sędzia" in joined
    assert "Kontraktowiec" in joined
    assert "keep the language" in joined.lower() or "same language" in joined.lower()


def test_style_profile_is_a_lens():
    profile = bundled_profile("norwegian_jante")
    block = profile.prompt_block("Target")
    assert "norwegian_jante" in block
    assert "Janteloven" in block or "jante" in block.lower()


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
    lens = AdHocLens(id="emi:x", name="EMI listener", summary="Match EMI.", lines=("emi3",))
    engine.translate(
        "Fix it.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        target_lens=lens,
    )
    system = llm.calls[0].messages[0]["content"]
    assert "EMI listener" in system
    assert "emi3" in system
