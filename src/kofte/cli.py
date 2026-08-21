"""Minimal CLI: list profiles, print a prompt. Translation needs an injected LLM."""

from __future__ import annotations

import argparse
import sys

from kofte.profiles import bundled_profile, list_profiles
from kofte.prompts import build_messages
from kofte.registers import parse_register
from kofte.translate import resolve_profile
from kofte.translate import translate as translate_message


def _cmd_profiles(_: argparse.Namespace) -> int:
    for name in list_profiles():
        profile = bundled_profile(name)
        supreme = ", ".join(axis.id for axis in profile.supreme)
        sys.stdout.write(f"{profile.id}\t{profile.name}\t{supreme}\n")
    return 0


def _cmd_prompt(args: argparse.Namespace) -> int:
    source = parse_register(args.source)
    target = parse_register(args.target)
    messages = build_messages(
        text=args.text,
        source=source,
        target=target,
        source_profile=resolve_profile(source, None),
        target_profile=resolve_profile(target, None),
    )
    for message in messages:
        sys.stdout.write(f"--- {message['role']} ---\n")
        sys.stdout.write(message["content"])
        sys.stdout.write("\n")
    return 0


def _cmd_translate(args: argparse.Namespace) -> int:
    try:
        result = translate_message(
            args.text,
            source=args.source,
            target=args.target,
        )
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        sys.stderr.write("Pass an LLM in Python: translate(..., llm=your_client)\n")
        return 2
    sys.stdout.write(result.text)
    sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kofte",
        description="Cultural style translator. Language and style are independent axes.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_profiles = sub.add_parser("profiles", help="list bundled style profiles")
    p_profiles.set_defaults(func=_cmd_profiles)

    p_prompt = sub.add_parser("prompt", help="print the assembled prompt, do not call an LLM")
    p_prompt.add_argument("text")
    p_prompt.add_argument("--source", required=True)
    p_prompt.add_argument("--target", required=True)
    p_prompt.set_defaults(func=_cmd_prompt)

    p_translate = sub.add_parser("translate", help="translate (requires an LLM in-process)")
    p_translate.add_argument("text")
    p_translate.add_argument("--source", required=True)
    p_translate.add_argument("--target", required=True)
    p_translate.set_defaults(func=_cmd_translate)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
