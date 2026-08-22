# Kofte

Open message-translation layer. Language and style are independent. A voice is a Lens.

A message has two axes: **language** and **style**. Kofte rewrites one, the other, or both. It is an engine other hosts sit on: Python, CLI, MCP, function-calling tools, Slack events, a browser selection, a clipboard.

Two shipped routes, same Polish source:

| source | target | what you get |
| --- | --- | --- |
| `pl+polish_direct` | `en+american_english` | English words, American agency |
| `pl+polish_direct` | `en+norwegian_jante` | English words, Janteloven register |
| `pl+polish_direct` | `nb+norwegian_jante` | Bokmål words, Janteloven register |
| `en+polish_direct` | `en+norwegian_jante` | style only, English stays English |
| `en+polish_direct` | `nb+polish_direct` | language only, blunt register stays |

## Install

```bash
uv add git+https://github.com/mikolaj92/Kofte.git
uv add 'kofte[mcp]'   # optional, for the MCP server
```

## Engine

```python
from kofte import OpenAICompatClient, Translator

# Any /v1 chat-completions server. Bearer token is optional.
llm = OpenAICompatClient(
    base_url="http://127.0.0.1:1234/v1",
    model="local-model",
)
engine = Translator(llm=llm)
result = engine.translate(
    "This is wrong. Fix it.",
    source="en+polish_direct",
    target="en+norwegian_jante",
)
print(result.text)
print(result.language_changed, result.style_changed)
```

One-shot helper still exists:

```python
from kofte import translate
```

Conversation context is a list of turns:

```python
from kofte import Turn

engine.translate(
    "This PR is a mess. Do it again.",
    source="en+polish_direct",
    target="en+norwegian_jante",
    context=[
        Turn(role="user", text="Could you review my pull request?"),
        Turn(role="assistant", text="Sure."),
    ],
)
```

## Lenses

A **Lens** is the voice the rewrite should match. Two sources, one engine:

- a **style folder** (`polish_direct`, `american_english`, `norwegian_jante`, your own pack)
- a **host-built trait list** (anything the host already knows)

The host builds a lens from traits. Kofte only renders it:

```python
from kofte import Translator, lens_from_traits

reviewer = lens_from_traits(
    "brief_reviewer",
    "Brief reviewer",
    [
        ("Tone", "dry"),
        ("Length", "two sentences"),
    ],
    summary="Short notes. Name the file.",
)
engine.translate(
    "This is wrong. Fix it.",
    source="en",
    target="en",
    target_lens=reviewer,
)
```

Source voice + target voice:

```python
engine.translate(
    text,
    source="en",
    target="en",
    source_lens=speaker,
    target_lens=listener,
)
```

`AdHocLens` is the same thing without the helper. `StyleProfile` is a Lens.

## Add a style pack (the “filter”)

A profile is a folder, not a class:

```
quiet_brit/
  profile.toml
  rules.md
  canon.md
  examples.md
  anti_patterns.md
```

```toml
id = "quiet_brit"
name = "Quiet British understatement"
language_hint = "en"
summary = "Understate, never boast, leave an exit."
supreme = ["understatement", "face"]

[[axes]]
id = "understatement"
name = "Understatement"
description = "Say less than you mean."

[[axes]]
id = "face"
name = "Face"
description = "Leave the other person a way out."
```

Register it, then address it by id:

```python
from kofte import load_profile

engine.registry.register(load_profile("path/to/quiet_brit"))
engine.translate(text, source="en+polish_direct", target="en+quiet_brit")
```

Or load a directory of packs:

```python
engine.registry.load_dir("path/to/packs")
```

CLI: `kofte --profile-dir path/to/packs profiles`

Shipped packs:

- `polish_direct` — supreme: **directness**, **productivity**
- `american_english` — supreme: **agency**, **positivity**
- `norwegian_jante` — supreme: **janteloven**, **egalitarianism**

## Pipeline filters

A filter is any object with optional `before(request)` / `after(result, request)`.

```python
from kofte import ForbiddenSubstringFilter, FunctionFilter, RequirePreservedFilter, Translator

engine = Translator(
    llm=llm,
    filters=[
        RequirePreservedFilter(),
        ForbiddenSubstringFilter(["garbage", "this is stupid"]),
        FunctionFilter(
            name="trim",
            after=lambda result, request: result.model_copy(update={"text": result.text.strip()}),
        ),
    ],
)
```

- `before` may rewrite the request (text, registers, context) before the LLM sees it.
- `after` may rewrite or reject the result (`FilterError`).
- No base class required. `FunctionFilter` wraps callables.

## MCP

A model can call Kofte as tools: `list_profiles`, `describe_profile`, `translate`.

```bash
uv run kofte mcp
# or
uv run kofte-mcp
```

Hermes / Claude / Cursor, stdio:

```yaml
mcp_servers:
  kofte:
    command: "uv"
    args: ["run", "--directory", "/path/to/Kofte", "kofte", "mcp"]
```

Or in Python:

```python
from kofte import OpenAICompatClient
from kofte.mcp_server import create_server
server = create_server(llm=OpenAICompatClient(base_url="http://127.0.0.1:1234/v1", model="local-model"))
```

## Function-calling tools (no MCP)

Same three tools, as JSON schema:

```python
from kofte import TOOLS, dispatch

# give TOOLS to your model as tools=
out = dispatch("translate", {
    "text": "This is wrong. Fix it.",
    "source": "en+polish_direct",
    "target": "en+norwegian_jante",
}, llm=llm)
```

## Hosts (Slack, browser, clipboard)

Kofte does not ship a Slack app or a Chrome extension. It ships the inbound seam those apps call.

```python
from kofte import Translator, from_slack, translate_inbound

inbound = from_slack(event, thread=thread_messages)
result = translate_inbound(engine, inbound, "en+polish_direct", "en+norwegian_jante")
```

```python
from kofte import from_browser, from_clipboard

from_clipboard("This is wrong. Fix it.")
from_browser({"selection": "This is wrong.", "page_url": "https://github.com/x/y/pull/1"})
```

Wire a Slack bot, a browser extension, or a clipboard watcher on top. The engine stays the same.

## CLI

```bash
kofte profiles
kofte prompt --source en+polish_direct --target en+norwegian_jante "This is wrong. Fix it."
kofte translate --json --source en+polish_direct --target en+norwegian_jante "This is wrong."
kofte mcp
```

`kofte translate` talks to any `/v1/chat/completions` server:

```bash
kofte translate --base-url http://127.0.0.1:1234/v1 --model qwen \
  --source en+polish_direct --target en+norwegian_jante "This is wrong. Fix it."
```

Env instead of flags: `KOFTE_LLM_BASE_URL`, `KOFTE_LLM_MODEL`, optional `KOFTE_LLM_API_KEY`.
LM Studio / Ollama / vLLM / llama.cpp is enough. There is no OpenAI default.

## Translation rules (Jante)

Rules live in the profile, not in Python. The Norwegian pack:

- keep the fact
- drop status
- prefer *we*
- leave a way out
- one or two clauses of why, not an essay, not their homework
- not a parody, not fake humility, not empty softness

The prompt also freezes: language and style are independent; preserve facts and work; do not add a solution.

The LLM writes the rewrite. Optional `after` filters can reject a bad one.

## Design

- **Registers** (`en+american_english`, `en+norwegian_jante`) split language from style.
- **Profiles** are TOML + Markdown. Culture is data.
- **Lenses** are any voice with `prompt_block`. A folder is one source. A host-built trait list is another.
- **Translator** is the reusable engine: registry + LLM + filters.
- **LLM** is a protocol. `OpenAICompatClient` talks HTTP to `{base_url}/chat/completions`. Bearer optional. No vendor default. Or inject your own.
- **MCP and TOOLS** are the same three calls.
- **Hosts** convert Slack / browser / clipboard into `InboundMessage`.

## Tests

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

## License

MIT
