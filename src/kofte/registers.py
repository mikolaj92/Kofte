"""Language and style are independent axes of a register."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, field_validator

_LANG_ALIASES = {"no": "nb"}
_REJECTED = {"xx", "und", "zxx", "mul", "mis", "zzz"}
_LANG_RE = re.compile(r"[a-z]{2,3}")


class Register(BaseModel):
    """A communication register: a language, plus an optional style profile id."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    language: str
    style: str | None = None

    @field_validator("language", mode="before")
    @classmethod
    def _normalize_language(cls, value: object) -> str:
        raw = str(value).strip().lower().replace("_", "-")
        primary = raw.split("-", 1)[0]
        primary = _LANG_ALIASES.get(primary, primary)
        if primary in _REJECTED or not _LANG_RE.fullmatch(primary):
            raise ValueError(f"unknown language {value!r}")
        return primary

    @field_validator("style", mode="before")
    @classmethod
    def _normalize_style(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def changes_language(self, other: Register) -> bool:
        return self.language != other.language

    def changes_style(self, other: Register) -> bool:
        return self.style != other.style


def parse_register(value: str | Register) -> Register:
    """Parse ``pl``, ``en+norwegian_jante``, or a Register."""
    if isinstance(value, Register):
        return value
    raw = value.strip()
    if "+" in raw:
        language, style = raw.split("+", 1)
        return Register(language=language, style=style)
    return Register(language=raw, style=None)
