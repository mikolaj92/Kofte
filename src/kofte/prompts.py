"""Deterministic prompt assembly. Language and style stay separate axes."""

from __future__ import annotations

from collections.abc import Sequence

from kofte.models import Turn
from kofte.profiles.schema import StyleProfile
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


def _block(title: str, lines: Sequence[str]) -> str:
    if not lines:
        return ""
    body = "\n".join(f"- {line}" for line in lines)
    return f"## {title}\n{body}"


def _profile_block(label: str, profile: StyleProfile) -> str:
    supreme = ", ".join(f"{axis.name} ({axis.id})" for axis in profile.supreme)
    parts = [
        f"# {label}: {profile.name} (`{profile.id}`)",
        profile.summary,
        f"Supreme axes: {supreme}. These override everything else.",
        _block("Axes", [f"{a.id}: {a.description or a.name}" for a in profile.axes]),
        _block("Rules", profile.rules),
        _block("Canon", profile.canon),
        _block("Examples", profile.examples),
        _block("Anti-patterns", profile.anti_patterns),
    ]
    return "\n\n".join(p for p in parts if p)


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


def _style_instruction(
    source: Register,
    target: Register,
    source_profile: StyleProfile | None,
    target_profile: StyleProfile | None,
) -> str:
    if source.style == target.style:
        if target_profile is None:
            return "Keep the style. Do not restyle."
        return f"Keep the style ({target_profile.name}). Do not restyle."
    src_name = source_profile.name if source_profile else (source.style or "the source style")
    dst_name = target_profile.name if target_profile else (target.style or "the target style")
    extra = ""
    if target_profile and any(axis.id == "janteloven" for axis in target_profile.supreme):
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
    source_profile: StyleProfile | None = None,
    target_profile: StyleProfile | None = None,
    context: Sequence[Turn] | None = None,
) -> list[dict[str, str]]:
    """Build the chat messages for one translation."""
    system_parts = [
        "You are a cultural style translator.",
        "A message has two independent axes: language and style.",
        "You may change language, style, both, or neither, exactly as the target register says.",
        "Preserve the facts. Preserve the work. Do not add a solution. Do not add tasks.",
        "Return JSON matching the given schema.",
        _language_instruction(source, target),
        _style_instruction(source, target, source_profile, target_profile),
    ]
    if source_profile is not None:
        system_parts.append(_profile_block("Source style", source_profile))
    if target_profile is not None:
        system_parts.append(_profile_block("Target style", target_profile))

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
