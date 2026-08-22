"""Language and style are independent axes of a register."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, field_validator

_LANG_ALIASES = {"no": "nb"}
_INFERRED = {"", "und", "auto", "*", "detect"}
_REJECTED = {"xx", "zxx", "mul", "mis", "zzz"}
_LANG_RE = re.compile(r"[a-z]{2,3}")


class Register(BaseModel):
    """A communication register: a language, plus an optional style profile id.

    ``language`` may be omitted. The engine then asks the LLM to detect it.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    language: str | None = None
    style: str | None = None

    @field_validator("language", mode="before")
    @classmethod
    def _normalize_language(cls, value: object) -> str | None:
        if value is None:
            return None
        raw = str(value).strip().lower().replace("_", "-")
        if raw in _INFERRED:
            return None
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


def parse_register(value: str | Register | None) -> Register:
    """Parse ``pl``, ``en+kofte``, ``auto``, or a Register.

    ``None``, ``auto``, and ``und`` mean: infer the language from the message.
    """
    if isinstance(value, Register):
        return value
    if value is None:
        return Register()
    raw = value.strip()
    if raw.lower() in _INFERRED:
        return Register()
    if "+" in raw:
        language, style = raw.split("+", 1)
        return Register(language=language or None, style=style)
    try:
        return Register(language=raw, style=None)
    except ValueError:
        return Register(language=None, style=raw)
