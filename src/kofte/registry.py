"""Name-keyed registry of style profiles.

Bundled profiles load by default. Hosts add more with ``register``,
``register_path``, or ``load_dir``. ``en+quiet_brit`` then resolves.
``kofte`` is an alias of the Norwegian pack.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

from kofte.errors import UnknownProfileError
from kofte.profiles import bundled_profile, list_profiles, load_profile
from kofte.profiles.schema import StyleProfile


class ProfileRegistry:
    """``style id -> StyleProfile`` with duplicate protection and aliases."""

    def __init__(self, profiles: Iterable[StyleProfile] = ()) -> None:
        self._entries: dict[str, StyleProfile] = {}
        self._aliases: dict[str, str] = {}
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
        if profile.id in self._aliases and not replace:
            raise KeyError(f"profile {profile.id!r} is already registered as an alias")
        for alias in profile.aliases:
            if alias == profile.id:
                continue
            taken = None
            if alias in self._entries:
                taken = self._entries[alias]
            elif alias in self._aliases:
                taken = self._entries[self._aliases[alias]]
            if taken is not None and taken.id != profile.id and not replace:
                raise KeyError(f"alias {alias!r} is already registered")
        if replace and profile.id in self._entries:
            old = self._entries[profile.id]
            for alias in old.aliases:
                self._aliases.pop(alias, None)
        self._entries[profile.id] = profile
        for alias in profile.aliases:
            if alias != profile.id:
                self._aliases[alias] = profile.id
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
        key = self._aliases.get(profile_id, profile_id)
        try:
            return self._entries[key]
        except KeyError as exc:
            raise UnknownProfileError(profile_id) from exc

    def __contains__(self, profile_id: object) -> bool:
        return profile_id in self._entries or profile_id in self._aliases

    def __len__(self) -> int:
        return len(self._entries)

    def names(self) -> list[str]:
        return sorted(self._entries)

    def items(self) -> list[tuple[str, StyleProfile]]:
        return sorted(self._entries.items(), key=lambda kv: kv[0])

    def __iter__(self) -> Iterator[StyleProfile]:
        for _, profile in self.items():
            yield profile
