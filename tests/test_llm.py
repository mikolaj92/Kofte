"""LLM protocol: scriptable mock and JSON schema round-trip."""

from __future__ import annotations

from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft


def test_mock_llm_returns_scripted_draft():
    draft = TranslationDraft(
        text="We can look at this together.",
        language="en",
        style="norwegian_jante",
        moves=["we"],
        preserved=["look"],
    )
    llm = MockLLMClient(responses=[draft])
    out = llm.complete_json(
        [{"role": "user", "content": "hello"}],
        TranslationDraft,
    )
    assert out.text == draft.text
    assert len(llm.calls) == 1
    assert llm.calls[0].messages[0]["content"] == "hello"


def test_mock_llm_accepts_plain_dicts():
    llm = MockLLMClient(
        responses=[
            {
                "text": "Vi kan se på dette.",
                "language": "nb",
                "style": "norwegian_jante",
                "moves": ["we"],
                "preserved": ["dette"],
            }
        ]
    )
    out = llm.complete_json([], TranslationDraft)
    assert out.language == "nb"
    assert out.text.startswith("Vi")
