"""Injectable filters. Before rewrites the request, after checks the result.

A filter is any object with optional ``before`` / ``after``. No base class
required. Use ``FunctionFilter`` for a one-liner.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, runtime_checkable

from kofte.errors import FilterError
from kofte.models import TranslationRequest, TranslationResult


@runtime_checkable
class Filter(Protocol):
    name: str

    def before(self, request: TranslationRequest) -> TranslationRequest: ...

    def after(
        self, result: TranslationResult, request: TranslationRequest
    ) -> TranslationResult: ...


def filter_name(filt: object) -> str:
    name = getattr(filt, "name", None)
    if isinstance(name, str) and name:
        return name
    return type(filt).__name__


def apply_before(filters: Sequence[object], request: TranslationRequest) -> TranslationRequest:
    current = request
    for filt in filters:
        before = getattr(filt, "before", None)
        if before is None:
            continue
        current = before(current)
    return current


def apply_after(
    filters: Sequence[object],
    result: TranslationResult,
    request: TranslationRequest,
) -> TranslationResult:
    current = result
    for filt in filters:
        after = getattr(filt, "after", None)
        if after is None:
            continue
        current = after(current, request)
    return current


class FunctionFilter:
    """Wrap callables as a filter."""

    def __init__(
        self,
        name: str = "function",
        before: Callable[[TranslationRequest], TranslationRequest] | None = None,
        after: Callable[[TranslationResult, TranslationRequest], TranslationResult] | None = None,
    ) -> None:
        self.name = name
        self._before = before
        self._after = after

    def before(self, request: TranslationRequest) -> TranslationRequest:
        if self._before is None:
            return request
        return self._before(request)

    def after(self, result: TranslationResult, request: TranslationRequest) -> TranslationResult:
        if self._after is None:
            return result
        return self._after(result, request)


class ForbiddenSubstringFilter:
    """Reject output that still contains banned substrings (case-insensitive)."""

    def __init__(self, needles: Sequence[str], name: str = "forbidden") -> None:
        self.name = name
        self.needles = tuple(n.lower() for n in needles if n)

    def after(self, result: TranslationResult, request: TranslationRequest) -> TranslationResult:
        text = result.text.lower()
        for needle in self.needles:
            if needle in text:
                raise FilterError(f"output still contains {needle!r}", self.name)
        return result


class RequirePreservedFilter:
    """Fail if the model claimed to preserve a fact that is missing from the text."""

    name = "require_preserved"

    def after(self, result: TranslationResult, request: TranslationRequest) -> TranslationResult:
        text = result.text.lower()
        for fact in result.preserved:
            if fact and fact.lower() not in text:
                raise FilterError(f"claimed preserved fact missing from output: {fact}", self.name)
        return result
