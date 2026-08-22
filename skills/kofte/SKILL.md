---
name: kofte
description: Rewrite a message from one language or form to another via the Kofte engine. Use when translating language (pl→en), restyling a register (polish_direct→norwegian_jante / american_english), or plugging Kofte in as MCP / CLI / function-calling tools.
license: MIT
---

# Kofte

Kofte is a translation engine. Language and form are independent.

- `pl` → `en` changes words.
- `en+polish_direct` → `en+norwegian_jante` changes form, English stays English.
- `target_form` is a free-text voice when there is no pack.

Do not invent a rewrite in the agent. Call the engine.

## Plug in (MCP)

Any MCP host:

```yaml
mcp_servers:
  kofte:
    command: "uv"
    args: ["run", "--directory", "/path/to/Kofte", "kofte", "mcp"]
```

Or: `uv run kofte-mcp` after `uv add 'kofte[mcp]'`.

Needs a `/v1/chat/completions` server:

```bash
export KOFTE_LLM_BASE_URL=http://127.0.0.1:1234/v1
export KOFTE_LLM_MODEL=local-model
# optional: KOFTE_LLM_API_KEY
```

Tools: `list_profiles`, `describe_profile`, `translate`.

## Plug in (CLI)

```bash
kofte translate --source pl --target en "To jest źle. Popraw to."
kofte translate --source pl+polish_direct --target en+american_english "To jest źle."
kofte translate --source pl+polish_direct --target en+norwegian_jante "To jest źle."
kofte translate --source en --target en --target-form "Brief reviewer. Name the file." "This is wrong. Fix it."
```

## Plug in (function calling)

```python
from kofte import TOOLS, dispatch
out = dispatch("translate", {"text": text, "source": "pl", "target": "en"}, llm=llm)
```

`target_form` / `source_form` are free-text voices. No pack required.

## Registers

`{language}` or `{language}+{style}`.

Shipped styles: `polish_direct`, `american_english`, `norwegian_jante`.
Unknown style is an error. Unknown language-only (`pl`, `en`) is fine.

Call `list_profiles` before guessing a style id.
