"""Shared fixtures."""

from __future__ import annotations

import pytest

from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft


@pytest.fixture
def canned_draft() -> TranslationDraft:
    return TranslationDraft(
        text="We might look at this again together. Something here does not work yet.",
        language="en",
        style="norwegian_jante",
        moves=["softened the verdict", "shifted blame off a person", "kept the fact"],
        preserved=["it does not work", "needs another pass"],
    )


@pytest.fixture
def mock_llm(canned_draft: TranslationDraft) -> MockLLMClient:
    return MockLLMClient(responses=[canned_draft])
