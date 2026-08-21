"""Optional OpenAI wrapper. Kofte does not import this on the default path."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OpenAIJSONClient:
    """Thin adapter: chat.completions → pydantic schema.

    Install extra: `uv add kofte[openai]` then:

        from examples.openai_client import OpenAIJSONClient
        from kofte import translate

        result = translate(
            "This is wrong. Fix it.",
            source="en+polish_direct",
            target="en+norwegian_jante",
            llm=OpenAIJSONClient(),
        )
    """

    def __init__(self, model: str = "gpt-4.1-mini", client: Any | None = None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.model = model

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
