"""Replaceable LLM. The library does not own a vendor."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel


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


class OpenAIJSONClient:
    """Thin OpenAI adapter: chat.completions → pydantic schema.

    Install extra: ``uv add 'kofte[openai]'``. Pass a pre-built client in tests.
    """

    def __init__(self, model: str | None = None, client: Any | None = None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.model = model or os.environ.get("KOFTE_LLM_MODEL", "gpt-4.1-mini")

    def complete_json(self, messages: list[dict[str, str]], schema: type[BaseModel]) -> BaseModel:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                },
            },
        )
        content = response.choices[0].message.content or "{}"
        return schema.model_validate_json(content)


def build_llm() -> LLMClient | None:
    """Build an LLM from the environment.

    ``KOFTE_LLM=none`` → None.
    ``OPENAI_API_KEY`` or ``KOFTE_LLM=openai`` → OpenAIJSONClient.
    Otherwise None. Hosts inject their own client.
    """
    kind = os.environ.get("KOFTE_LLM", "").strip().lower()
    if kind in {"none", "off", "0"}:
        return None
    if kind == "mock":
        return MockLLMClient()
    if kind in {"openai", "openai-json"} or os.environ.get("OPENAI_API_KEY"):
        return OpenAIJSONClient()
    return None
