"""Profile registry: bundled + user profiles resolve by style id."""

from __future__ import annotations

from pathlib import Path

import pytest

from kofte.errors import UnknownProfileError
from kofte.profiles import load_profile
from kofte.registry import ProfileRegistry


def _quiet_brit(tmp_path: Path):
    folder = tmp_path / "quiet_brit"
    folder.mkdir()
    (folder / "profile.toml").write_text(
        """
id = "quiet_brit"
name = "Quiet British understatement"
language_hint = "en"
summary = "Understate, never boast, leave an exit."
supreme = ["understatement"]

[[axes]]
id = "understatement"
name = "Understatement"
description = "Say less than you mean."
""".lstrip()
    )
    (folder / "rules.md").write_text("- Hedge.\n")
    return folder


def test_bundled_registry_has_jante_and_polish():
    registry = ProfileRegistry.bundled()
    assert "norwegian_jante" in registry
    assert "polish_direct" in registry
    assert "american_english" in registry
    assert registry.get("norwegian_jante").id == "norwegian_jante"
    assert registry.get("american_english").id == "american_english"


def test_register_custom_profile_then_resolve_by_id(tmp_path: Path):
    registry = ProfileRegistry.bundled()
    profile = load_profile(_quiet_brit(tmp_path))
    registry.register(profile)
    assert registry.get("quiet_brit").name.startswith("Quiet")


def test_register_path_and_load_dir(tmp_path: Path):
    folder = _quiet_brit(tmp_path)
    registry = ProfileRegistry()
    registry.register_path(folder)
    assert "quiet_brit" in registry

    parent = tmp_path / "pack"
    other = parent / "loud_us"
    other.mkdir(parents=True)
    (other / "profile.toml").write_text(
        """
id = "loud_us"
name = "Loud US"
language_hint = "en"
summary = "Say it big."
supreme = ["volume"]
[[axes]]
id = "volume"
name = "Volume"
description = "Be loud."
""".lstrip()
    )
    registry.load_dir(parent)
    assert "loud_us" in registry
    assert "quiet_brit" in registry


def test_duplicate_register_raises(tmp_path: Path):
    registry = ProfileRegistry.bundled()
    with pytest.raises(KeyError, match="already"):
        registry.register(registry.get("norwegian_jante"))


def test_unknown_profile_raises():
    registry = ProfileRegistry.bundled()
    with pytest.raises(UnknownProfileError, match="quiet_brit"):
        registry.get("quiet_brit")


def test_replace_allows_override(tmp_path: Path):
    registry = ProfileRegistry.bundled()
    profile = load_profile(_quiet_brit(tmp_path))
    registry.register(profile)
    registry.register(profile, replace=True)
    assert registry.get("quiet_brit").id == "quiet_brit"


def test_kofte_alias_resolves_norwegian_jante():
    registry = ProfileRegistry.bundled()
    assert registry.get("kofte") is registry.get("norwegian_jante")
    assert "kofte" in registry
