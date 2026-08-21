"""Kofte — open cultural style-translation layer.

A message has two axes: language and style. You can change one, the other, or both.

The shipped example is Polish directness and productivity → Norwegian
Janteloven and egalitarianism. Other cultures are data folders. Hosts
(Slack, browser, MCP, CLI) sit on top of :class:`Translator`.
"""

from kofte.engine import Translator, translate
from kofte.errors import FilterError, KofteError, LLMNotConfiguredError, UnknownProfileError
from kofte.filters import Filter, ForbiddenSubstringFilter, FunctionFilter, RequirePreservedFilter
from kofte.hosts import InboundMessage, from_browser, from_clipboard, from_slack, translate_inbound
from kofte.llm import LLMClient, MockLLMClient, OpenAIJSONClient, build_llm
from kofte.models import TranslationDraft, TranslationRequest, TranslationResult, Turn
from kofte.profiles import StyleProfile, bundled_profile, list_profiles, load_profile
from kofte.registers import Register, parse_register
from kofte.registry import ProfileRegistry
from kofte.tools import TOOLS, dispatch

__version__ = "0.2.0"

__all__ = [
    "TOOLS",
    "Filter",
    "FilterError",
    "ForbiddenSubstringFilter",
    "FunctionFilter",
    "InboundMessage",
    "KofteError",
    "LLMClient",
    "LLMNotConfiguredError",
    "MockLLMClient",
    "OpenAIJSONClient",
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
    "list_profiles",
    "load_profile",
    "parse_register",
    "translate",
    "__version__",
]
