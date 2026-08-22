"""Kofte — open message-translation layer.

A message has two axes: language and style. You can change one, the other, or both.
A voice is a Lens: a style folder, or a host-built trait list.

Kofte is a Norwegian word. The shipped Norwegian voice is addressable
as ``kofte`` (alias of ``norwegian_jante``). Compose hops to change
language, then form: ``pl → en → en+kofte``.
"""

from kofte.engine import Translator, translate
from kofte.errors import FilterError, KofteError, LLMNotConfiguredError, UnknownProfileError
from kofte.filters import Filter, ForbiddenSubstringFilter, FunctionFilter, RequirePreservedFilter
from kofte.hosts import InboundMessage, from_browser, from_clipboard, from_slack, translate_inbound
from kofte.lenses import AdHocLens, Lens, lens_from_traits
from kofte.llm import LLMClient, MockLLMClient, OpenAICompatClient, build_llm
from kofte.models import TranslationDraft, TranslationRequest, TranslationResult, Turn
from kofte.profiles import StyleProfile, bundled_profile, list_profiles, load_profile
from kofte.registers import Register, parse_register
from kofte.registry import ProfileRegistry
from kofte.tools import TOOLS, dispatch

__version__ = "0.3.3"

__all__ = [
    "TOOLS",
    "AdHocLens",
    "Filter",
    "FilterError",
    "ForbiddenSubstringFilter",
    "FunctionFilter",
    "InboundMessage",
    "KofteError",
    "LLMClient",
    "LLMNotConfiguredError",
    "Lens",
    "MockLLMClient",
    "OpenAICompatClient",
    "ProfileRegistry",
    "Register",
    "RequirePreservedFilter",
    "StyleProfile",
    "TranslationDraft",
    "TranslationRequest",
    "TranslationResult",
    "Translator",
    "Turn",
    "UnknownProfileError",
    "build_llm",
    "bundled_profile",
    "dispatch",
    "from_browser",
    "from_clipboard",
    "from_slack",
    "translate_inbound",
    "lens_from_traits",
    "list_profiles",
    "load_profile",
    "parse_register",
    "translate",
    "__version__",
]
