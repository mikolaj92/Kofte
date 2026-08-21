"""Replaceable LLM. Any /v1 chat-completions endpoint. Bearer token optional."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urljoin

from pydantic import BaseModel

Transport = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


class LLMClient(Protocol):
    def complete_json(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
    ) -> BaseModel: ...


@dataclass(frozen=True)
class LLMCall:
    messages: list[dict[str, str]]
    schema: type[BaseModel]


class MockLLMClient:
    """Scriptable LLM for tests and examples."""

    def __init__(self, responses: Sequence[BaseModel | Mapping[str, Any]] | None = None) -> None:
        self._responses = list(responses or [])
        self.calls: list[LLMCall] = []

    def complete_json(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
    ) -> BaseModel:
        self.calls.append(LLMCall(messages=messages, schema=schema))
        if not self._responses:
            raise RuntimeError("MockLLMClient has no remaining responses")
        response = self._responses.pop(0)
        if isinstance(response, BaseModel):
            return schema.model_validate(response.model_dump(mode="json"))
        return schema.model_validate(response)


class OpenAICompatClient:
    """HTTP client for any server that speaks ``/v1/chat/completions``.

    LM Studio, Ollama, vLLM, llama.cpp, and similar. Talks to
    ``{base_url}/chat/completions``. No vendor SDK. ``api_key`` is an
    optional bearer for servers that ask for one — it is not an OpenAI key.
    """

    class HTTPError(RuntimeError):
        def __init__(self, status: int, body: str) -> None:
            self.status = status
            self.body = body
            super().__init__(f"HTTP {status}: {body[:500]}")

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 120.0,
        json_mode: str = "auto",
        transport: Transport | None = None,
    ) -> None:
        if not model:
            raise ValueError("model is required")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or None
        self.timeout = timeout
        if json_mode not in {"auto", "schema", "off"}:
            raise ValueError("json_mode must be auto, schema, or off")
        self.json_mode = json_mode
        self._transport = transport or self._http_transport

    def complete_json(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
    ) -> BaseModel:
        payload: dict[str, Any] = {"model": self.model, "messages": messages}
        want_schema = self.json_mode in {"auto", "schema"}
        if want_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                },
            }
        try:
            raw = self._post(payload)
        except OpenAICompatClient.HTTPError:
            if self.json_mode != "auto" or "response_format" not in payload:
                raise
            fallback = dict(payload)
            fallback.pop("response_format", None)
            raw = self._post(fallback)
        return _parse_message(raw, schema)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = _join_chat_url(self.base_url)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return self._transport(url, headers, payload)

    def _http_transport(
        self, url: str, headers: dict[str, str], payload: dict[str, Any]
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise OpenAICompatClient.HTTPError(exc.code, body) from exc


def _join_chat_url(base_url: str) -> str:
    base = base_url if base_url.endswith("/") else base_url + "/"
    return urljoin(base, "chat/completions")


def _parse_message(raw: Mapping[str, Any], schema: type[BaseModel]) -> BaseModel:
    try:
        content = raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"unexpected chat completions payload: {raw!r}") from exc
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, Mapping) else str(part) for part in content
        )
    if not isinstance(content, str):
        content = json.dumps(content)
    text = _strip_fences(content)
    return schema.model_validate_json(text)


def _strip_fences(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def build_llm(
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> LLMClient | None:
    """Build an LLM from arguments or the environment.

    ``KOFTE_LLM=none`` → None.
    ``KOFTE_LLM=mock`` → MockLLMClient.
    Otherwise a /v1 chat-completions server:

    - ``KOFTE_LLM_BASE_URL`` / ``base_url`` (required)
    - ``KOFTE_LLM_MODEL`` / ``model`` (required)
    - ``KOFTE_LLM_API_KEY`` / ``api_key`` (optional bearer)

    No default URL. No vendor key names. No default model.
    """
    kind = os.environ.get("KOFTE_LLM", "").strip().lower()
    if kind in {"none", "off", "0"}:
        return None
    if kind == "mock":
        return MockLLMClient()

    url = (base_url or os.environ.get("KOFTE_LLM_BASE_URL") or "").strip()
    name = (model or os.environ.get("KOFTE_LLM_MODEL") or "").strip()
    key = (api_key or os.environ.get("KOFTE_LLM_API_KEY") or "").strip() or None
    if not url or not name:
        return None
    return OpenAICompatClient(base_url=url, model=name, api_key=key)
