"""Back-compat entry: ``translate()`` and ``resolve_profile()``.

New hosts should use :class:`kofte.engine.Translator`.
"""

from __future__ import annotations

from kofte.engine import Translator
from kofte.engine import translate as translate
from kofte.profiles import bundled_profile
from kofte.profiles.schema import StyleProfile
from kofte.registers import Register

__all__ = ["Translator", "resolve_profile", "translate"]


def resolve_profile(register: Register, override: StyleProfile | None) -> StyleProfile | None:
    """Resolve a bundled profile. Prefer Translator.resolve on a real engine."""
    if override is not None:
        return override
    if not register.style:
        return None
    try:
        return bundled_profile(register.style)
    except KeyError:
        return None
