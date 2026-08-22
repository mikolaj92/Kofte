"""CLI: list profiles, print a prompt, translate, run MCP."""

from __future__ import annotations

import argparse
import json
import sys

from kofte.engine import Translator
from kofte.errors import KofteError, LLMNotConfiguredError
from kofte.lenses import AdHocLens
from kofte.llm import build_llm
from kofte.prompts import build_messages
from kofte.registers import parse_register
from kofte.registry import ProfileRegistry
from kofte.tools import result_payload


def _parse_hops(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    return parts or None


def _form_lens(role: str, brief: str | None):
    if not brief or not str(brief).strip():
        return None
    name = "Source form" if role == "source" else "Target form"
    return AdHocLens(id=f"form:{role}", name=name, summary=str(brief).strip())


def _engine(args: argparse.Namespace) -> Translator:
    registry = ProfileRegistry.bundled()
    extra = getattr(args, "profile_dir", None)
    if extra:
        registry.load_dir(extra)
    llm = build_llm(
        base_url=getattr(args, "base_url", None),
        model=getattr(args, "model", None),
        api_key=getattr(args, "api_key", None),
    )
    return Translator(llm=llm, registry=registry)


def _cmd_profiles(args: argparse.Namespace) -> int:
    engine = _engine(args)
    for profile in engine.registry:
        supreme = ", ".join(axis.id for axis in profile.supreme)
        aliases = ",".join(profile.aliases)
        extra = f"\t{aliases}" if aliases else ""
        sys.stdout.write(f"{profile.id}\t{profile.name}\t{supreme}{extra}\n")
    return 0


def _cmd_prompt(args: argparse.Namespace) -> int:
    engine = _engine(args)
    source = parse_register(args.source)
    target = parse_register(args.target)
    messages = build_messages(
        text=args.text,
        source=source,
        target=target,
        source_profile=engine.resolve(source, None),
        target_profile=engine.resolve(target, None),
    )
    for message in messages:
        sys.stdout.write(f"--- {message['role']} ---\n")
        sys.stdout.write(message["content"])
        sys.stdout.write("\n")
    return 0


def _cmd_translate(args: argparse.Namespace) -> int:
    engine = _engine(args)
    try:
        hops = _parse_hops(getattr(args, "hops", None))
        result = engine.translate(
            args.text,
            source=args.source,
            target=args.target,
            source_lens=_form_lens("source", getattr(args, "source_form", None)),
            target_lens=_form_lens("target", getattr(args, "target_form", None)),
            hops=hops,
        )
    except LLMNotConfiguredError as exc:
        sys.stderr.write(f"{exc}\n")
        sys.stderr.write(
            "Pass --base-url and --model for any /v1 chat-completions server "
            "(LM Studio, Ollama, vLLM, llama.cpp). Bearer token is optional.\n"
        )
        return 2
    except (KofteError, ValueError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    if args.json:
        sys.stdout.write(json.dumps(result_payload(result), ensure_ascii=False))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(result.text)
        sys.stdout.write("\n")
    return 0


def _cmd_mcp(args: argparse.Namespace) -> int:
    from kofte.mcp_server import create_server

    engine = _engine(args)
    server = create_server(translator=engine)
    server.run("stdio")
    return 0


def _add_profile_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile-dir",
        help="Load extra style profiles from subfolders of this directory.",
    )


def _add_llm_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base-url",
        help="Chat-completions API root, e.g. http://127.0.0.1:1234/v1. "
        "Overrides KOFTE_LLM_BASE_URL.",
    )
    parser.add_argument(
        "--model",
        help="Model id on that server. Overrides KOFTE_LLM_MODEL.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional bearer token. Local servers usually do not need one.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kofte",
        description="Message translator. Language and form are independent axes.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_profiles = sub.add_parser("profiles", help="list style profiles")
    _add_profile_dir(p_profiles)
    p_profiles.set_defaults(func=_cmd_profiles)

    p_prompt = sub.add_parser("prompt", help="print the assembled prompt, do not call an LLM")
    p_prompt.add_argument("text")
    p_prompt.add_argument("--source", required=True)
    p_prompt.add_argument("--target", required=True)
    _add_profile_dir(p_prompt)
    p_prompt.set_defaults(func=_cmd_prompt)

    p_translate = sub.add_parser(
        "translate",
        help="translate a message via any /v1 chat-completions server",
    )
    p_translate.add_argument("text")
    p_translate.add_argument("--source", default=None)
    p_translate.add_argument("--target", default=None)
    p_translate.add_argument(
        "--hops",
        help="One-pass path, comma-separated: pl,en,en+kofte",
    )
    p_translate.add_argument("--json", action="store_true", help="print a JSON result")
    p_translate.add_argument(
        "--source-form",
        help="Free-text source voice when there is no profile folder.",
    )
    p_translate.add_argument(
        "--target-form",
        help="Free-text target voice when there is no profile folder.",
    )
    _add_profile_dir(p_translate)
    _add_llm_flags(p_translate)
    p_translate.set_defaults(func=_cmd_translate)

    p_mcp = sub.add_parser("mcp", help="run the MCP server on stdio")
    _add_profile_dir(p_mcp)
    _add_llm_flags(p_mcp)
    p_mcp.set_defaults(func=_cmd_mcp)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
