"""Public translation entry: message + registers + optional context → rewrite."""

from __future__ import annotations

from collections.abc import Sequence

from kofte.llm import LLMClient
from kofte.models import TranslationDraft, TranslationResult, Turn
from kofte.profiles import StyleProfile, bundled_profile
from kofte.prompts import build_messages
from kofte.registers import Register, parse_register


def resolve_profile(register: Register, override: StyleProfile | None) -> StyleProfile | None:
    if override is not None:
        return override
    if not register.style:
        return None
    try:
        return bundled_profile(register.style)
    except KeyError:
        return None


def translate(
    text: str,
    source: str | Register,
    target: str | Register,
    context: Sequence[Turn] | None = None,
    llm: LLMClient | None = None,
    source_profile: StyleProfile | None = None,
    target_profile: StyleProfile | None = None,
) -> TranslationResult:
    """Rewrite ``text`` from ``source`` register to ``target`` register.

    Language and style are independent. ``en+norwegian_jante`` is English
    words in a Norwegian Jante register. ``nb+polish_direct`` is the reverse.

    An LLM client must be supplied. Kofte does not own a vendor.
    """
    if llm is None:
        raise RuntimeError("llm is required")

    source_reg = parse_register(source)
    target_reg = parse_register(target)
    src_profile = resolve_profile(source_reg, source_profile)
    dst_profile = resolve_profile(target_reg, target_profile)

    messages = build_messages(
        text=text,
        source=source_reg,
        target=target_reg,
        source_profile=src_profile,
        target_profile=dst_profile,
        context=context,
    )
    draft = llm.complete_json(messages, TranslationDraft)
    if not isinstance(draft, TranslationDraft):
        draft = TranslationDraft.model_validate(draft)

    return TranslationResult(
        text=draft.text,
        source=source_reg,
        target=target_reg,
        original=text,
        moves=tuple(draft.moves),
        preserved=tuple(draft.preserved),
    )
