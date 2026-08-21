"""TOML + Markdown profile schema."""

from __future__ import annotations

import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class StyleAxis(BaseModel):
    """One cultural axis the profile treats as real, e.g. Janteloven."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""


class StyleProfile(BaseModel):
    """A named cultural style: supreme axes, rules, and source canon."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    language_hint: str
    summary: str
    axes: tuple[StyleAxis, ...]
    supreme: tuple[StyleAxis, ...]
    rules: tuple[str, ...] = ()
    canon: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    anti_patterns: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _supreme_must_exist(self) -> StyleProfile:
        known = {axis.id for axis in self.axes}
        missing = [axis.id for axis in self.supreme if axis.id not in known]
        if missing:
            raise ValueError(f"supreme axes not defined: {missing}")
        return self


def _read_text(folder: Any, name: str) -> str:
    path = folder / name
    if hasattr(path, "is_file") and not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, AttributeError, OSError):
        return ""


def _md_bullets(text: str) -> tuple[str, ...]:
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith(("- ", "* ")):
            lines.append(stripped[2:].strip())
        elif stripped.startswith("#"):
            continue
        elif stripped:
            lines.append(stripped)
    return tuple(lines)


def load_profile_from_path(folder: Path | Any) -> StyleProfile:
    raw_toml = _read_text(folder, "profile.toml")
    if not raw_toml:
        raise FileNotFoundError("profile.toml")
    data = tomllib.loads(raw_toml)

    axes = tuple(StyleAxis.model_validate(item) for item in data.get("axes", []))
    by_id = {axis.id: axis for axis in axes}
    supreme_ids: Iterable[str] = data.get("supreme", [])
    try:
        supreme = tuple(by_id[item] for item in supreme_ids)
    except KeyError as exc:
        raise ValueError(f"supreme axis {exc.args[0]!r} is not in axes") from exc

    rules = _md_bullets(_read_text(folder, "rules.md"))
    canon = _md_bullets(_read_text(folder, "canon.md"))
    examples = _md_bullets(_read_text(folder, "examples.md"))
    anti = _md_bullets(_read_text(folder, "anti_patterns.md"))

    return StyleProfile(
        id=data["id"],
        name=data["name"],
        language_hint=data["language_hint"],
        summary=data["summary"],
        axes=axes,
        supreme=supreme,
        rules=rules,
        canon=canon,
        examples=examples,
        anti_patterns=anti,
    )
