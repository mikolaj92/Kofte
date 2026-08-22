"""Kofte — open message-translation layer.

A message has two axes: language and style. You can change one, the other, or both.
A voice is a Lens: a style folder, or a host-built trait list.

Shipped examples: Polish directness → American English, and Polish
directness → Norwegian Janteloven (English or Bokmål). Hosts (Slack,
browser, MCP, CLI) sit on top of :class:`Translator`.
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

__version__ = "0.3.1"

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
