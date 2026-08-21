"""Name-keyed registry of style profiles.

Bundled profiles load by default. Hosts add more with ``register``,
``register_path``, or ``load_dir``. ``en+quiet_brit`` then resolves.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

from kofte.errors import UnknownProfileError
from kofte.profiles import bundled_profile, list_profiles, load_profile
from kofte.profiles.schema import StyleProfile


class ProfileRegistry:
    """``style id -> StyleProfile`` with duplicate protection."""

    def __init__(self, profiles: Iterable[StyleProfile] = ()) -> None:
        self._entries: dict[str, StyleProfile] = {}
        for profile in profiles:
            self.register(profile)

    @classmethod
    def bundled(cls) -> ProfileRegistry:
        registry = cls()
        for profile_id in list_profiles():
            registry.register(bundled_profile(profile_id))
        return registry

    def register(self, profile: StyleProfile, *, replace: bool = False) -> StyleProfile:
        if profile.id in self._entries and not replace:
            raise KeyError(f"profile {profile.id!r} is already registered")
        self._entries[profile.id] = profile
        return profile

    def register_path(self, folder: str | Path, *, replace: bool = False) -> StyleProfile:
        return self.register(load_profile(folder), replace=replace)

    def load_dir(self, root: str | Path, *, replace: bool = False) -> list[StyleProfile]:
        """Load every immediate subdirectory that contains profile.toml."""
        loaded: list[StyleProfile] = []
        for child in sorted(Path(root).iterdir()):
            if child.is_dir() and (child / "profile.toml").is_file():
                loaded.append(self.register_path(child, replace=replace))
        return loaded

    def get(self, profile_id: str) -> StyleProfile:
        try:
            return self._entries[profile_id]
        except KeyError as exc:
            raise UnknownProfileError(profile_id) from exc

    def __contains__(self, profile_id: object) -> bool:
        return profile_id in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def names(self) -> list[str]:
        return sorted(self._entries)

    def items(self) -> list[tuple[str, StyleProfile]]:
        return sorted(self._entries.items(), key=lambda kv: kv[0])

    def __iter__(self) -> Iterator[StyleProfile]:
        for _, profile in self.items():
            yield profile
