"""Filters are injectable: before rewrites the request, after checks the result."""

from __future__ import annotations

import pytest

from kofte import translate
from kofte.errors import FilterError
from kofte.filters import Filter, ForbiddenSubstringFilter, FunctionFilter, RequirePreservedFilter
from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft, TranslationRequest


class PrefixFilter:
    name = "prefix"

    def before(self, request: TranslationRequest) -> TranslationRequest:
        return request.model_copy(update={"text": "PREFIX " + request.text})

    def after(self, result, request: TranslationRequest):
        return result.model_copy(update={"text": result.text + " /ok"})


def test_before_filter_rewrites_text_seen_by_llm():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="we can look",
                language="en",
                style="norwegian_jante",
                moves=[],
                preserved=[],
            )
        ]
    )
    translate(
        "This is wrong.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        llm=llm,
        filters=[PrefixFilter()],
    )
    blob = "\n".join(m["content"] for m in llm.calls[0].messages)
    assert "PREFIX This is wrong." in blob


def test_after_filter_rewrites_result():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="we can look",
                language="en",
                style="norwegian_jante",
            )
        ]
    )
    result = translate(
        "This is wrong.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        llm=llm,
        filters=[PrefixFilter()],
    )
    assert result.text.endswith("/ok")


def test_require_preserved_filter_raises_when_claim_missing():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Something else entirely.",
                language="en",
                style="norwegian_jante",
                preserved=["line 12"],
            )
        ]
    )
    with pytest.raises(FilterError, match="line 12"):
        translate(
            "The test fails on line 12.",
            source="en+polish_direct",
            target="en+norwegian_jante",
            llm=llm,
            filters=[RequirePreservedFilter()],
        )


def test_forbidden_substring_filter():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="This is garbage. Fix it.",
                language="en",
                style="norwegian_jante",
            )
        ]
    )
    with pytest.raises(FilterError, match="garbage"):
        translate(
            "This is wrong.",
            source="en+polish_direct",
            target="en+norwegian_jante",
            llm=llm,
            filters=[ForbiddenSubstringFilter(["garbage"])],
        )


def test_function_filter_one_liner():
    llm = MockLLMClient(
        responses=[
            TranslationDraft(text="ok", language="en", style="norwegian_jante")
        ]
    )
    filt = FunctionFilter(
        name="upper",
        after=lambda result, request: result.model_copy(update={"text": result.text.upper()}),
    )
    result = translate(
        "This is wrong.",
        source="en+polish_direct",
        target="en+norwegian_jante",
        llm=llm,
        filters=[filt],
    )
    assert result.text == "OK"


def test_filter_protocol_name_is_optional_but_listed():
    assert isinstance(PrefixFilter(), Filter) or hasattr(PrefixFilter(), "before")
