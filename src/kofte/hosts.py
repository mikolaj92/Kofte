"""Inbound adapters. The library does not speak Slack or Chrome.

Hosts convert their native event into ``InboundMessage``, then call
``Translator.translate``. Ship a Slack bot, a browser extension, or a
clipboard watcher on top of this — Kofte stays the engine.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from kofte.models import Turn


class InboundMessage(BaseModel):
    """A message arriving from any host."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    host: str = "generic"
    source_id: str | None = None
    context: tuple[Turn, ...] = ()
    extra: dict[str, Any] = Field(default_factory=dict)


def from_slack(
    event: Mapping[str, Any],
    thread: Sequence[Mapping[str, Any]] | None = None,
) -> InboundMessage:
    """Slack ``message`` event → InboundMessage.

    ``thread`` is the ordered history (oldest first). Bot messages become
    assistant turns; everyone else is user. The current event is the text,
    not context.
    """
    text = str(event.get("text") or "")
    channel = str(event.get("channel") or "")
    ts = str(event.get("ts") or event.get("thread_ts") or "")
    source_id = f"slack:{channel}:{ts}" if channel or ts else "slack"
    context: list[Turn] = []
    event_ts = event.get("ts")
    for item in thread or ():
        if event_ts is not None and item.get("ts") == event_ts:
            continue
        item_text = str(item.get("text") or "")
        if not item_text:
            continue
        role = "assistant" if item.get("bot_id") else "user"
        context.append(Turn(role=role, text=item_text))
    return InboundMessage(
        text=text,
        host="slack",
        source_id=source_id,
        context=tuple(context),
        extra={"channel": channel, "user": event.get("user")},
    )


def from_clipboard(text: str) -> InboundMessage:
    return InboundMessage(text=text, host="clipboard", source_id="clipboard")


def from_browser(payload: Mapping[str, Any]) -> InboundMessage:
    """Browser-extension payload: selected text + optional page URL + turns."""
    text = str(payload.get("selection") or payload.get("text") or "")
    url = str(payload.get("page_url") or payload.get("url") or "")
    raw_context = payload.get("context") or ()
    context: list[Turn] = []
    for item in raw_context:
        if isinstance(item, Turn):
            context.append(item)
            continue
        role = str(item.get("role") or "user")
        if role not in {"user", "assistant", "system"}:
            role = "user"
        context.append(Turn(role=role, text=str(item.get("text") or "")))
    return InboundMessage(
        text=text,
        host="browser",
        source_id=url or "browser",
        context=tuple(context),
        extra={"page_url": url},
    )



def translate_inbound(engine: Any, inbound: InboundMessage, source: str, target: str) -> Any:
    """Run an engine on a host message, forwarding conversation context."""
    return engine.translate(
        inbound.text,
        source=source,
        target=target,
        context=inbound.context,
    )
