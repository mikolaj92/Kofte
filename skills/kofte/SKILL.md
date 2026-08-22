---
name: kofte
description: Rewrite a message from one language or form to another via the Kofte engine. Use when translating language (pl→en), restyling into the Norwegian Kofte voice (en+kofte), output hops (en+kofte), or plugging Kofte in as MCP / CLI / function-calling tools.
license: MIT
---

# Kofte

Kofte is a Norwegian word and a translation engine. Language and form are independent.

- `pl` → `en` changes words.
- `en` → `en+kofte` keeps English, applies the Norwegian voice (Janteloven).
- hops are outputs. `en+kofte` is enough. Source language is optional; the model detects it.
- `kofte` is the built-in alias of `norwegian_jante`.
- `target_form` is a free-text voice when there is no pack.

Do not invent a rewrite in the agent. Call the engine.

## Plug in (MCP)

```yaml
mcp_servers:
  kofte:
    command: "uv"
    args: ["run", "--directory", "/path/to/Kofte", "kofte", "mcp"]
```

Or: `uv run kofte-mcp` after `uv add 'kofte[mcp]'`.

```bash
export KOFTE_LLM_BASE_URL=http://127.0.0.1:1234/v1
export KOFTE_LLM_MODEL=local-model
```

Tools: `list_profiles`, `describe_profile`, `translate`.

## Plug in (CLI)

```bash
kofte translate --source pl --target en "To jest źle. Popraw to."
kofte translate --source en --target en+kofte "This is wrong. Fix it."
kofte translate --hops en+kofte "To jest źle. Popraw to."
kofte translate --source pl+polish_direct --target en+american_english "To jest źle."
kofte translate --source en --target en --target-form "Brief reviewer. Name the file." "This is wrong. Fix it."
```

## Plug in (function calling)

```python
from kofte import TOOLS, dispatch
out = dispatch("translate", {"text": text, "hops": ["en+kofte"]}, llm=llm)
```

## Registers

`{language}` or `{language}+{style}`.

Shipped styles: `kofte` (Norwegian; alias of `norwegian_jante`), `polish_direct`, `american_english`.
Unknown style is an error. Language-only (`pl`, `en`) is fine.

Call `list_profiles` before guessing a style id.
