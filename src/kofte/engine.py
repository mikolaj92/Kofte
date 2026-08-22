"""Reusable translation engine: registry + LLM + filters + lenses."""

from __future__ import annotations

from collections.abc import Sequence

from kofte.errors import LLMNotConfiguredError, UnknownProfileError
from kofte.filters import apply_after, apply_before
from kofte.lenses import Lens
from kofte.llm import LLMClient
from kofte.models import TranslationDraft, TranslationRequest, TranslationResult, Turn
from kofte.prompts import build_messages
from kofte.registers import Register, parse_register
from kofte.registry import ProfileRegistry


class Translator:
    """A configured style translator you can reuse across hosts.

    Bundled profiles are loaded by default. Register more, inject filters,
    swap the LLM. Pass a Lens (folder or host-built trait list) when the
    voice is not a register style id.
    """

    def __init__(
        self,
        llm: LLMClient | None = None,
        registry: ProfileRegistry | None = None,
        filters: Sequence[object] = (),
    ) -> None:
        self.llm = llm
        self.registry = registry if registry is not None else ProfileRegistry.bundled()
        self.filters: list[object] = list(filters)

    def resolve(
        self, register: Register, override: Lens | None = None
    ) -> Lens | None:
        if override is not None:
            return override
        if not register.style:
            return None
        return self.registry.get(register.style)

    def translate(
        self,
        text: str,
        source: str | Register,
        target: str | Register,
        context: Sequence[Turn] | None = None,
        llm: LLMClient | None = None,
        source_profile: Lens | None = None,
        target_profile: Lens | None = None,
        source_lens: Lens | None = None,
        target_lens: Lens | None = None,
        filters: Sequence[object] | None = None,
    ) -> TranslationResult:
        client = llm if llm is not None else self.llm
        if client is None:
            raise LLMNotConfiguredError("llm is required")

        request = TranslationRequest(
            text=text,
            source=parse_register(source),
            target=parse_register(target),
            context=tuple(context or ()),
        )
        chain = list(self.filters if filters is None else filters)
        request = apply_before(chain, request)

        src_override = source_lens or source_profile
        dst_override = target_lens or target_profile
        try:
            src = self.resolve(request.source, src_override)
        except UnknownProfileError:
            if src_override is not None:
                src = src_override
            else:
                raise
        try:
            dst = self.resolve(request.target, dst_override)
        except UnknownProfileError:
            if dst_override is not None:
                dst = dst_override
            else:
                raise

        messages = build_messages(
            text=request.text,
            source=request.source,
            target=request.target,
            source_lens=src,
            target_lens=dst,
            context=request.context,
        )
        draft = client.complete_json(messages, TranslationDraft)
        if not isinstance(draft, TranslationDraft):
            draft = TranslationDraft.model_validate(draft)

        result = TranslationResult(
            text=draft.text,
            source=request.source,
            target=request.target,
            original=text,
            moves=tuple(draft.moves),
            preserved=tuple(draft.preserved),
        )
        return apply_after(chain, result, request)


def translate(
    text: str,
    source: str | Register,
    target: str | Register,
    context: Sequence[Turn] | None = None,
    llm: LLMClient | None = None,
    source_profile: Lens | None = None,
    target_profile: Lens | None = None,
    source_lens: Lens | None = None,
    target_lens: Lens | None = None,
    filters: Sequence[object] | None = None,
    registry: ProfileRegistry | None = None,
) -> TranslationResult:
    """One-shot translation. Builds a Translator with bundled profiles."""
    engine = Translator(llm=llm, registry=registry, filters=filters or ())
    return engine.translate(
        text,
        source=source,
        target=target,
        context=context,
        source_profile=source_profile,
        target_profile=target_profile,
        source_lens=source_lens,
        target_lens=target_lens,
    )
