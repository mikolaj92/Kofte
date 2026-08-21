"""OpenAI-compatible HTTP client: any /v1 endpoint, API key optional."""

from __future__ import annotations

import json

import pytest

from kofte.llm import OpenAICompatClient, build_llm
from kofte.models import TranslationDraft


def _ok_payload(text: str = "ok") -> dict:
    body = {
        "text": text,
        "language": "en",
        "style": "norwegian_jante",
        "moves": [],
        "preserved": [],
    }
    return {"choices": [{"message": {"content": json.dumps(body)}}]}


def test_posts_to_custom_base_url_without_authorization():
    calls: list[dict] = []

    def transport(url: str, headers: dict[str, str], payload: dict) -> dict:
        calls.append({"url": url, "headers": headers, "payload": payload})
        return _ok_payload()

    client = OpenAICompatClient(
        base_url="http://127.0.0.1:1234/v1",
        model="local-model",
        transport=transport,
    )
    out = client.complete_json([{"role": "user", "content": "hi"}], TranslationDraft)
    assert out.text == "ok"
    assert calls[0]["url"] == "http://127.0.0.1:1234/v1/chat/completions"
    assert "Authorization" not in calls[0]["headers"]
    assert calls[0]["payload"]["model"] == "local-model"


def test_optional_api_key_sends_bearer():
    calls: list[dict] = []

    def transport(url: str, headers: dict[str, str], payload: dict) -> dict:
        calls.append({"headers": headers})
        return _ok_payload()

    OpenAICompatClient(
        base_url="http://localhost:8080/v1",
        model="x",
        api_key="secret",
        transport=transport,
    ).complete_json([], TranslationDraft)
    assert calls[0]["headers"]["Authorization"] == "Bearer secret"


def test_strips_markdown_fences():
    def transport(url, headers, payload):
        body = json.dumps({"text": "we look", "language": "en", "style": "norwegian_jante"})
        return {"choices": [{"message": {"content": f"```json\n{body}\n```"}}]}

    out = OpenAICompatClient(
        base_url="http://localhost/v1",
        model="x",
        transport=transport,
    ).complete_json([], TranslationDraft)
    assert out.text == "we look"


def test_falls_back_when_json_schema_rejected():
    calls: list[dict] = []

    def transport(url: str, headers: dict[str, str], payload: dict) -> dict:
        calls.append(payload)
        if "response_format" in payload:
            raise OpenAICompatClient.HTTPError(400, "unknown response_format")
        return _ok_payload("fallback")

    out = OpenAICompatClient(
        base_url="http://localhost/v1",
        model="x",
        json_mode="auto",
        transport=transport,
    ).complete_json([{"role": "user", "content": "hi"}], TranslationDraft)
    assert out.text == "fallback"
    assert "response_format" in calls[0]
    assert "response_format" not in calls[1]


def test_build_llm_from_base_url_does_not_need_api_key(monkeypatch):
    monkeypatch.setenv("KOFTE_LLM_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("KOFTE_LLM_MODEL", "qwen")
    llm = build_llm()
    assert isinstance(llm, OpenAICompatClient)
    assert llm.base_url.endswith("/v1")
    assert llm.model == "qwen"
    assert llm.api_key is None


def test_build_llm_none_without_url(monkeypatch):
    monkeypatch.delenv("KOFTE_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("KOFTE_LLM_MODEL", raising=False)
    monkeypatch.delenv("KOFTE_LLM_API_KEY", raising=False)
    monkeypatch.delenv("KOFTE_LLM", raising=False)
    assert build_llm() is None


def test_build_llm_cli_overrides_env(monkeypatch):
    monkeypatch.setenv("KOFTE_LLM_BASE_URL", "http://env/v1")
    monkeypatch.setenv("KOFTE_LLM_MODEL", "env-model")
    llm = build_llm(base_url="http://cli/v1", model="cli-model")
    assert isinstance(llm, OpenAICompatClient)
    assert llm.base_url == "http://cli/v1"
    assert llm.model == "cli-model"


def test_missing_model_with_url_raises():
    with pytest.raises(ValueError, match="model"):
        OpenAICompatClient(base_url="http://localhost/v1", model="")



def test_build_llm_url_without_model_is_none(monkeypatch):
    monkeypatch.delenv("KOFTE_LLM_MODEL", raising=False)
    monkeypatch.delenv("KOFTE_LLM", raising=False)
    monkeypatch.setenv("KOFTE_LLM_BASE_URL", "http://127.0.0.1:1234/v1")
    assert build_llm() is None


def test_openai_api_key_env_is_ignored(monkeypatch):
    monkeypatch.delenv("KOFTE_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("KOFTE_LLM_MODEL", raising=False)
    monkeypatch.delenv("KOFTE_LLM_API_KEY", raising=False)
    monkeypatch.delenv("KOFTE_LLM", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-not-used")
    llm = build_llm()
    assert llm is None
