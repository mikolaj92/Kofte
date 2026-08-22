"""A Lens is anything that can describe how to rewrite a message.

Style folders (Janteloven, Polish directness) and host-built views
(EMI traits, a one-off brief) are two sources of the same thing.
Kofte does not own EMI. The host builds a lens from traits.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict


@runtime_checkable
class Lens(Protocol):
    """Minimal voice: an id, a name, and a prompt block."""

    id: str
    name: str

    def prompt_block(self, label: str) -> str: ...


class AdHocLens(BaseModel):
    """A lens built in memory. Use this for EMI, or any host that
    already has traits and does not want a profile folder.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    summary: str = ""
    lines: tuple[str, ...] = ()

    def prompt_block(self, label: str) -> str:
        parts = [f"# {label}: {self.name} (`{self.id}`)"]
        if self.summary:
            parts.append(self.summary)
        if self.lines:
            body = "\n".join(f"- {line}" for line in self.lines)
            parts.append(f"## Traits\n{body}")
        return "\n\n".join(parts)


def lens_from_traits(
    lens_id: str,
    name: str,
    traits: Sequence[tuple[str, str]],
    summary: str = "",
) -> AdHocLens:
    """Build a lens from ``(category, label)`` pairs.

    Emitype would pass ``("Osobowość", "Kontraktowiec")`` etc.
    Kofte never imports emitype.
    """
    lines = tuple(f"{category}: {label}" for category, label in traits if label)
    return AdHocLens(id=lens_id, name=name, summary=summary, lines=lines)
