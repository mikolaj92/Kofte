"""Style profiles are data folders, not Python classes.

A profile is a TOML file plus optional Markdown. The library ships three:
Polish directness, American English, and Norwegian Janteloven.
Anything else is a folder you pass to ``load_profile``.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from kofte.profiles.schema import StyleAxis, StyleProfile, load_profile_from_path

_BUNDLED_PACKAGE = "kofte.profiles"


def list_profiles() -> list[str]:
    """Ids of profiles shipped with the library."""
    root = resources.files(_BUNDLED_PACKAGE)
    names: list[str] = []
    for entry in root.iterdir():
        if entry.is_dir() and (entry / "profile.toml").is_file():
            names.append(entry.name)
    return sorted(names)


def bundled_profile(profile_id: str) -> StyleProfile:
    """Load a shipped profile by id."""
    root = resources.files(_BUNDLED_PACKAGE)
    folder = root / profile_id
    if not (folder / "profile.toml").is_file():
        raise KeyError(f"unknown bundled profile {profile_id!r}")
    # importlib.abc.Traversable is enough for read_text; load via a real path
    # when we have one, else via the traversable reader.
    return load_profile_from_path(folder)


def load_profile(folder: str | Path) -> StyleProfile:
    """Load a user-authored profile from a directory containing profile.toml."""
    return load_profile_from_path(Path(folder))


__all__ = [
    "StyleAxis",
    "StyleProfile",
    "bundled_profile",
    "list_profiles",
    "load_profile",
]
