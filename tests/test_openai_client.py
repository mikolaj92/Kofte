"""OpenAI adapter lives in the package, not only in examples."""

from __future__ import annotations

from kofte.llm import OpenAIJSONClient
from kofte.models import TranslationDraft


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = type("M", (), {"content": content})()


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        payload = '{"text":"ok","language":"en","style":"norwegian_jante"}'
        return type("R", (), {"choices": [_Choice(payload)]})()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = type("C", (), {"completions": _FakeCompletions()})()


def test_openai_json_client_round_trips_schema():
    fake = _FakeClient()
    client = OpenAIJSONClient(client=fake, model="test-model")
    out = client.complete_json(
        [{"role": "user", "content": "hi"}],
        TranslationDraft,
    )
    assert out.text == "ok"
    call = fake.chat.completions.calls[0]
    assert call["model"] == "test-model"
    assert call["response_format"]["type"] == "json_schema"
