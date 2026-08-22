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


def language_name(code: str | None) -> str:
    if not code:
        return "the language of the message"
    return _LANGUAGE_NAMES.get(code, code)


def _register_label(register: Register) -> str:
    lang = language_name(register.language) if register.language else "detected language"
    if register.style:
        return f"{lang} + {register.style}"
    return lang


def _hops_instruction(
    hops: Sequence[Register] | None, source: Register | None = None
) -> str:
    if not hops:
        return ""
    path = " → ".join(_register_label(item) for item in hops)
    infer = source is None or source.language is None
    infer_bit = (
        "Infer the input language from the original message. " if infer else ""
    )
    if len(hops) == 1:
        return (
            f"Output: {path}. {infer_bit}"
            "Do this in one pass. Do not write an intermediate version. "
            "Facts come from the original."
        )
    return (
        f"Outputs: {path}. {infer_bit}"
        "Do this in one pass from the original. "
        "Do not write an intermediate version. Do not play telephone. "
        "Facts come from the original, not from a half-translated draft."
    )


def _language_instruction(source: Register, target: Register) -> str:
    if source.language is None and target.language is None:
        return (
            "Detect the language of the original message. "
            "Keep that language in the output unless a hop names a language."
        )
    if source.language is None:
        dst = language_name(target.language)
        return (
            "Detect the language of the original message. "
            f"The output language is {dst}."
        )
    src = language_name(source.language)
    if target.language is None or source.language == target.language:
        dst = language_name(target.language or source.language)
        return (
            f"Keep the language. The output must stay in {dst}. "
            "Do not translate the language. Rewrite style only."
        )
    dst = language_name(target.language)
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
    hops: Sequence[Register] | None = None,
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
        _hops_instruction(hops, source),
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
