"""Deterministic prompt assembly. Language and style stay separate axes."""

from __future__ import annotations

from collections.abc import Sequence

from kofte.lenses import Lens
from kofte.models import Turn
from kofte.registers import Register

_LANGUAGE_NAMES = {
    "pl": "Polish",
    "en": "English",
    "nb": "Norwegian Bokmål",
    "nn": "Norwegian Nynorsk",
    "da": "Danish",
    "sv": "Swedish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
}


def language_name(code: str) -> str:
    return _LANGUAGE_NAMES.get(code, code)


def _language_instruction(source: Register, target: Register) -> str:
    src = language_name(source.language)
    dst = language_name(target.language)
    if source.language == target.language:
        return (
            f"Keep the language. The output must stay in {dst}. "
            "Do not translate the language. Rewrite style only."
        )
    return (
        f"Translate the language from {src} to {dst}. "
        f"The output language is {dst}."
    )


def _lens_id(lens: Lens | None, register: Register) -> str | None:
    if lens is not None:
        return lens.id
    return register.style


def _style_instruction(
    source: Register,
    target: Register,
    source_lens: Lens | None,
    target_lens: Lens | None,
) -> str:
    src_id = _lens_id(source_lens, source)
    dst_id = _lens_id(target_lens, target)
    if src_id == dst_id:
        if target_lens is None:
            return "Keep the style. Do not restyle."
        return f"Keep the style ({target_lens.name}). Do not restyle."
    src_name = source_lens.name if source_lens else (source.style or "the source style")
    dst_name = target_lens.name if target_lens else (target.style or "the target style")
    extra = ""
    supreme = getattr(target_lens, "supreme", ())
    if any(getattr(axis, "id", None) == "janteloven" for axis in supreme):
        extra = (
            " Janteloven and egalitarianism are supreme. Do not parody. "
            "This is not a parody of Norway and not a cartoon of Jante. "
            "Keep the facts. Drop status. Prefer we. Leave a way out."
        )
    return f"Rewrite the style from {src_name} to {dst_name}.{extra}"


def build_messages(
    text: str,
    source: Register,
    target: Register,
    source_profile: Lens | None = None,
    target_profile: Lens | None = None,
    source_lens: Lens | None = None,
    target_lens: Lens | None = None,
    context: Sequence[Turn] | None = None,
) -> list[dict[str, str]]:
    """Build the chat messages for one translation.

    ``source_profile`` / ``target_profile`` are aliases for lenses
    (style folders). Any object with ``prompt_block`` works, including
    a trait list built by the host.
    """
    source_lens = source_lens or source_profile
    target_lens = target_lens or target_profile
    system_parts = [
        "You are a message translator.",
        "A message has two independent axes: language and style.",
        "A voice (lens) may be a culture pack or a host-built trait list.",
        "You may change language, style, both, or neither, exactly as the target register says.",
        "Preserve the facts. Preserve the work. Do not add a solution. Do not add tasks.",
        "Return JSON matching the given schema.",
        _language_instruction(source, target),
        _style_instruction(source, target, source_lens, target_lens),
    ]
    if source_lens is not None:
        system_parts.append(source_lens.prompt_block("Source style"))
    if target_lens is not None:
        system_parts.append(target_lens.prompt_block("Target style"))

    system = "\n\n".join(p for p in system_parts if p)

    user_parts: list[str] = []
    if context:
        rendered = "\n".join(f"{turn.role}: {turn.text}" for turn in context)
        user_parts.append("Conversation context:\n" + rendered)
    user_parts.append("Message to translate:\n" + text)
    user = "\n\n".join(user_parts)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
