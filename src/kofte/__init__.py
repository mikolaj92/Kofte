"""Kofte — open cultural style-translation layer.

A message has two axes: language and style. You can change one, the other, or both.

The shipped example is Polish directness and productivity → Norwegian
Janteloven and egalitarianism. Other cultures are data folders.
"""

from kofte.llm import LLMClient, MockLLMClient
from kofte.models import TranslationDraft, TranslationResult, Turn
from kofte.profiles import StyleProfile, bundled_profile, list_profiles, load_profile
from kofte.registers import Register, parse_register
from kofte.translate import translate

__version__ = "0.1.0"

__all__ = [
    "LLMClient",
    "MockLLMClient",
    "Register",
    "StyleProfile",
    "TranslationDraft",
    "TranslationResult",
    "Turn",
    "bundled_profile",
    "list_profiles",
    "load_profile",
    "parse_register",
    "translate",
    "__version__",
]
