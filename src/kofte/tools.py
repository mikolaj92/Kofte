"""OpenAI-style tool schema + dispatch.

Same three tools the MCP server exposes, so a model can call Kofte
through function-calling without speaking MCP.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from kofte.engine import Translator
from kofte.lenses import AdHocLens, Lens
from kofte.llm import LLMClient
from kofte.models import TranslationResult, Turn
from kofte.profiles.schema import StyleProfile
from kofte.registers import Register
from kofte.registry import ProfileRegistry

_TRANSLATE_PARAMS = {
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "The message to rewrite."},
        "source": {
            "type": "string",
            "description": "Source register, e.g. pl, en, pl+polish_direct.",
        },
        "target": {
            "type": "string",
            "description": "Target register, e.g. en, pl, en+american_english, en+norwegian_jante.",
        },
        "source_form": {
            "type": "string",
            "description": "Optional free-text source voice. Use when there is no profile folder.",
        },
        "target_form": {
            "type": "string",
            "description": "Optional free-text target voice. Use when there is no profile folder.",
        },
        "context": {
            "type": "array",
            "description": "Optional prior turns: [{role, text}, ...].",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                    "text": {"type": "string"},
                },
                "required": ["role", "text"],
            },
        },
    },
    "required": ["text", "source", "target"],
}

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_profiles",
            "description": "List registered Kofte style profiles (language/style packs).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_profile",
            "description": "Show rules, canon, and supreme axes for one style profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_id": {
                        "type": "string",
                        "description": "Profile id, e.g. norwegian_jante.",
                    }
                },
                "required": ["profile_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate",
            "description": (
                "Rewrite a message from one language/form to another. "
                "Language and style are independent: pl→en changes words; "
                "en+polish_direct→en+norwegian_jante changes register; "
                "target_form rewrites into a free-text voice with no pack."
            ),
            "parameters": _TRANSLATE_PARAMS,
        },
    },
]



def _form_lens(role: str, brief: object | None) -> Lens | None:
    if brief is None:
        return None
    text = str(brief).strip()
    if not text:
        return None
    name = "Source form" if role == "source" else "Target form"
    return AdHocLens(id=f"form:{role}", name=name, summary=text)


def register_code(register: Register) -> str:
    if register.style:
        return f"{register.language}+{register.style}"
    return register.language


def profile_summary(profile: StyleProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "name": profile.name,
        "language_hint": profile.language_hint,
        "summary": profile.summary,
        "supreme": [axis.id for axis in profile.supreme],
    }


def profile_detail(profile: StyleProfile) -> dict[str, Any]:
    return {
        **profile_summary(profile),
        "rules": list(profile.rules),
        "canon": list(profile.canon),
        "examples": list(profile.examples),
        "anti_patterns": list(profile.anti_patterns),
    }


def result_payload(result: TranslationResult) -> dict[str, Any]:
    return {
        "text": result.text,
        "original": result.original,
        "source": register_code(result.source),
        "target": register_code(result.target),
        "language_changed": result.language_changed,
        "style_changed": result.style_changed,
        "moves": list(result.moves),
        "preserved": list(result.preserved),
    }


def _turns(raw: Sequence[Mapping[str, Any]] | None) -> list[Turn]:
    if not raw:
        return []
    return [Turn(role=item["role"], text=item["text"]) for item in raw]


def _engine(llm: LLMClient | None, translator: Translator | None) -> Translator:
    if translator is not None:
        if llm is not None:
            translator.llm = llm
        return translator
    return Translator(llm=llm, registry=ProfileRegistry.bundled())


def dispatch(
    name: str,
    arguments: Mapping[str, Any],
    *,
    llm: LLMClient | None = None,
    translator: Translator | None = None,
) -> dict[str, Any]:
    """Run one tool by name. Used by MCP and by OpenAI-style function calling."""
    engine = _engine(llm, translator)
    if name == "list_profiles":
        return {"profiles": [profile_summary(p) for p in engine.registry]}
    if name == "describe_profile":
        profile = engine.registry.get(str(arguments["profile_id"]))
        return profile_detail(profile)
    if name == "translate":
        result = engine.translate(
            str(arguments["text"]),
            source=str(arguments["source"]),
            target=str(arguments["target"]),
            context=_turns(arguments.get("context")),
            source_lens=_form_lens("source", arguments.get("source_form")),
            target_lens=_form_lens("target", arguments.get("target_form")),
        )
        return result_payload(result)
    raise KeyError(f"unknown tool {name!r}")
