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


def _hop_chain(
    source: str | Register | None,
    target: str | Register | None,
    hops: Sequence[str | Register] | None,
) -> list[Register]:
    if hops:
        chain = [parse_register(item) for item in hops]
        if source is not None:
            start = parse_register(source)
            if not chain or chain[0] != start:
                chain = [start, *chain]
        if target is not None:
            end = parse_register(target)
            if chain[-1] != end:
                chain.append(end)
        if len(chain) < 2:
            raise ValueError("hops needs at least two registers, e.g. pl,en,en+kofte")
        return chain
    if source is None or target is None:
        raise ValueError("source and target are required unless hops is set")
    return [parse_register(source), parse_register(target)]


class Translator:
    """A configured style translator you can reuse across hosts.

    Bundled profiles are loaded by default. Register more, inject filters,
    swap the LLM. Pass a Lens when the voice is not a register style id.

    hops=["pl", "en", "en+kofte"] is one pass: original Polish in, English
    Kofte out. Intermediate hops are the path, not extra LLM calls.
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
        source: str | Register | None = None,
        target: str | Register | None = None,
        context: Sequence[Turn] | None = None,
        llm: LLMClient | None = None,
        source_profile: Lens | None = None,
        target_profile: Lens | None = None,
        source_lens: Lens | None = None,
        target_lens: Lens | None = None,
        filters: Sequence[object] | None = None,
        hops: Sequence[str | Register] | None = None,
    ) -> TranslationResult:
        client = llm if llm is not None else self.llm
        if client is None:
            raise LLMNotConfiguredError("llm is required")

        chain = _hop_chain(source, target, hops)
        src_override = source_lens or source_profile
        dst_override = target_lens or target_profile
        return self._one(
            text=text,
            source=chain[0],
            target=chain[-1],
            original=text,
            context=context,
            client=client,
            source_lens=src_override,
            target_lens=dst_override,
            filters=filters,
            hops=chain,
        )

    def _one(
        self,
        text: str,
        source: Register,
        target: Register,
        original: str,
        context: Sequence[Turn] | None,
        client: LLMClient,
        source_lens: Lens | None,
        target_lens: Lens | None,
        filters: Sequence[object] | None,
        hops: Sequence[Register] | None = None,
    ) -> TranslationResult:
        request = TranslationRequest(
            text=text,
            source=source,
            target=target,
            context=tuple(context or ()),
        )
        chain = list(self.filters if filters is None else filters)
        request = apply_before(chain, request)

        try:
            src = self.resolve(request.source, source_lens)
        except UnknownProfileError:
            if source_lens is not None:
                src = source_lens
            else:
                raise
        try:
            dst = self.resolve(request.target, target_lens)
        except UnknownProfileError:
            if target_lens is not None:
                dst = target_lens
            else:
                raise

        messages = build_messages(
            text=request.text,
            source=request.source,
            target=request.target,
            source_lens=src,
            target_lens=dst,
            context=request.context,
            hops=hops,
        )
        draft = client.complete_json(messages, TranslationDraft)
        if not isinstance(draft, TranslationDraft):
            draft = TranslationDraft.model_validate(draft)

        result = TranslationResult(
            text=draft.text,
            source=request.source,
            target=request.target,
            original=original,
            moves=tuple(draft.moves),
            preserved=tuple(draft.preserved),
        )
        return apply_after(chain, result, request)


def translate(
    text: str,
    source: str | Register | None = None,
    target: str | Register | None = None,
    context: Sequence[Turn] | None = None,
    llm: LLMClient | None = None,
    source_profile: Lens | None = None,
    target_profile: Lens | None = None,
    source_lens: Lens | None = None,
    target_lens: Lens | None = None,
    filters: Sequence[object] | None = None,
    registry: ProfileRegistry | None = None,
    hops: Sequence[str | Register] | None = None,
) -> TranslationResult:
    """One-shot translation. Builds a Translator with bundled profiles.

    ``hops=["pl", "en", "en+kofte"]`` is one pass from the original.
    Intermediate hops name the path. They are not extra LLM calls.
    """
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
        hops=hops,
    )
