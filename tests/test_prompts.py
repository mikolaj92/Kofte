"""Prompt assembly is deterministic and keeps language vs style split."""

from __future__ import annotations

from kofte.models import Turn
from kofte.profiles import bundled_profile
from kofte.prompts import build_messages
from kofte.registers import Register


def test_system_prompt_contains_jante_laws_and_forbids_parody():
    source = bundled_profile("polish_direct")
    target = bundled_profile("norwegian_jante")
    messages = build_messages(
        text="This is wrong. Fix it.",
        source=Register(language="en", style="polish_direct"),
        target=Register(language="en", style="norwegian_jante"),
        source_profile=source,
        target_profile=target,
    )
    system = messages[0]["content"]
    assert messages[0]["role"] == "system"
    assert "Janteloven" in system or "Jante" in system
    assert "egalitarian" in system.lower()
    assert "do not parody" in system.lower() or "not a parody" in system.lower()
    assert "keep the facts" in system.lower() or "preserve the facts" in system.lower()
    assert "language" in system.lower()
    assert "style" in system.lower()


def test_style_only_translation_asks_to_keep_the_language():
    source = bundled_profile("polish_direct")
    target = bundled_profile("norwegian_jante")
    messages = build_messages(
        text="This is wrong. Fix it now.",
        source=Register(language="en", style="polish_direct"),
        target=Register(language="en", style="norwegian_jante"),
        source_profile=source,
        target_profile=target,
    )
    joined = "\n".join(m["content"] for m in messages).lower()
    assert "keep the language" in joined or "same language" in joined
    assert "english" in joined


def test_language_and_style_both_change_for_polish_to_norwegian():
    source = bundled_profile("polish_direct")
    target = bundled_profile("norwegian_jante")
    messages = build_messages(
        text="To jest źle. Popraw to.",
        source=Register(language="pl", style="polish_direct"),
        target=Register(language="nb", style="norwegian_jante"),
        source_profile=source,
        target_profile=target,
    )
    joined = "\n".join(m["content"] for m in messages).lower()
    assert "norwegian" in joined or "bokmål" in joined or "norsk" in joined
    assert "polish" in joined or "polsk" in joined


def test_conversation_context_is_included():
    source = bundled_profile("polish_direct")
    target = bundled_profile("norwegian_jante")
    context = [
        Turn(role="user", text="Can you look at my PR?"),
        Turn(role="assistant", text="Yes."),
    ]
    messages = build_messages(
        text="This is garbage. Rewrite it.",
        source=Register(language="en", style="polish_direct"),
        target=Register(language="en", style="norwegian_jante"),
        source_profile=source,
        target_profile=target,
        context=context,
    )
    joined = "\n".join(m["content"] for m in messages)
    assert "look at my PR" in joined
    assert "garbage" in joined
