"""Public data shapes for a style translation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from kofte.registers import Register


class Turn(BaseModel):
    """One turn of optional conversation context."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["user", "assistant", "system"]
    text: str


class Message(BaseModel):
    """A message plus optional surrounding conversation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    context: tuple[Turn, ...] = ()


class TranslationDraft(BaseModel):
    """Structured LLM output. Facts in, register out."""

    text: str
    language: str
    style: str | None = None
    moves: list[str] = Field(default_factory=list)
    preserved: list[str] = Field(default_factory=list)


class TranslationResult(BaseModel):
    """Finished translation: text plus what changed on each axis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    source: Register
    target: Register
    original: str
    moves: tuple[str, ...] = ()
    preserved: tuple[str, ...] = ()

    @property
    def language_changed(self) -> bool:
        return self.target.changes_language(self.source)

    @property
    def style_changed(self) -> bool:
        return self.target.changes_style(self.source)
