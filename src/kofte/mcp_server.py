"""MCP server. A model calls list_profiles / describe_profile / translate.

    uv run kofte-mcp
    # or: uv run python -m kofte.mcp_server

Optional extra: ``kofte[mcp]``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from kofte.engine import Translator
from kofte.llm import LLMClient, build_llm
from kofte.registry import ProfileRegistry
from kofte.tools import dispatch


def create_server(
    llm: LLMClient | None = None,
    translator: Translator | None = None,
) -> Any:
    """Build an MCP server bound to a Translator."""
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise ImportError("kofte MCP support requires extra 'mcp': uv add kofte[mcp]") from exc

    engine = translator or Translator(llm=llm, registry=ProfileRegistry.bundled())
    if llm is not None:
        engine.llm = llm

    server = MCPServer(
        name="kofte",
        version="0.3.2",
        instructions=(
            "Message translator. Language and style are independent. "
            "Use list_profiles, describe_profile, then translate. "
            "pl→en changes language. en+polish_direct→en+norwegian_jante changes form. "
            "target_form is a free-text voice when there is no pack. "
            "en+norwegian_jante means English words in a Norwegian Jante register."
        ),
    )

    def _call(name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        return dispatch(name, arguments, translator=engine)

    @server.tool()
    def list_profiles() -> dict[str, Any]:
        """List registered Kofte style profiles."""
        return _call("list_profiles", {})

    @server.tool()
    def describe_profile(profile_id: str) -> dict[str, Any]:
        """Show rules, canon, and supreme axes for one style profile."""
        return _call("describe_profile", {"profile_id": profile_id})

    @server.tool()
    def translate(
        text: str,
        source: str,
        target: str,
        source_form: str | None = None,
        target_form: str | None = None,
        context: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Rewrite a message from one language/form to another."""
        payload: dict[str, Any] = {"text": text, "source": source, "target": target}
        if source_form:
            payload["source_form"] = source_form
        if target_form:
            payload["target_form"] = target_form
        if context:
            payload["context"] = context
        return _call("translate", payload)

    return server


def main() -> None:
    server = create_server(llm=build_llm())
    server.run("stdio")


if __name__ == "__main__":
    main()
