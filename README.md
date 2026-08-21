# Kofte

Open cultural style-translation layer.

A message has two axes: **language** and **style**. Kofte rewrites one, the other, or both.

The only shipped, fully worked example is:

> Polish — language of directness and productivity
> → Norwegian — Janteloven + egalitarianism as the supreme traits.

That is a *style* translation, not only a language translation. These are all legal:

| source | target | what changes |
| --- | --- | --- |
| `pl+polish_direct` | `nb+norwegian_jante` | language and style |
| `pl+polish_direct` | `en+norwegian_jante` | language to English, style to Jante |
| `en+polish_direct` | `en+norwegian_jante` | style only, English stays English |
| `en+polish_direct` | `nb+polish_direct` | language only, blunt register stays |

The library is the same shape as the emitype translator: a message (plus optional conversation context) goes through a profile ontology and comes out rewritten. Profiles are data folders. The LLM is injected. Kofte does not own a vendor.

## Install

```bash
uv add git+https://github.com/mikolaj92/Kofte.git
```

or

```bash
pip install git+https://github.com/mikolaj92/Kofte.git
```

## Usage

```python
from kofte import MockLLMClient, TranslationDraft, translate

llm = MockLLMClient(
    responses=[
        TranslationDraft(
            text="Something here does not work yet. We could look at it again together.",
            language="en",
            style="norwegian_jante",
            moves=["we instead of you", "softened the verdict"],
            preserved=["does not work"],
        )
    ]
)

result = translate(
    "This is wrong. Fix it.",
    source="en+polish_direct",
    target="en+norwegian_jante",
    llm=llm,
)

print(result.text)
print(result.language_changed, result.style_changed)
```

With conversation context:

```python
from kofte import Turn, translate

result = translate(
    "This PR is a mess. Do it again.",
    source="en+polish_direct",
    target="en+norwegian_jante",
    context=[
        Turn(role="user", text="Could you review my pull request?"),
        Turn(role="assistant", text="Sure."),
    ],
    llm=llm,
)
```

Wire any LLM that implements `complete_json(messages, schema) -> BaseModel`. A 15-line OpenAI wrapper is in `examples/openai_client.py`.

## CLI

```bash
kofte profiles
kofte prompt --source en+polish_direct --target en+norwegian_jante "This is wrong. Fix it."
```

`kofte translate` exists but refuses to run without an in-process LLM. The library will not smuggle a default vendor.

## What a profile is

A folder:

```
profile.toml    # id, name, language_hint, summary, supreme axes
rules.md        # how to write
canon.md        # source material (for Jante: the ten laws)
examples.md
anti_patterns.md
```

Shipped:

- `polish_direct` — supreme axes: **directness**, **productivity**
- `norwegian_jante` — supreme axes: **janteloven**, **egalitarianism**

Load your own:

```python
from kofte import load_profile, translate

quiet = load_profile("path/to/quiet_brit")
result = translate(
    "This is wrong. Fix it.",
    source="en+polish_direct",
    target="en+quiet_brit",
    target_profile=quiet,
    llm=llm,
)
```

## Janteloven, not a parody

The Norwegian profile treats Sandemose's ten laws as canon, then reads them as workplace egalitarianism:

- keep the fact
- drop status
- prefer *we*
- leave a way out
- one or two clauses of why, not an essay, not their homework

It is not a cartoon of Norway. Fake humility ("I am probably wrong, but…") is an anti-pattern. Empty softness that deletes the fact is a failed translation.

## Design

Same idea as the emitype translator: the production path is a second reading of the same message, through an ontology, into a description in another register.

- **Registers** (`en+norwegian_jante`) split language from style.
- **Profiles** are TOML + Markdown. Code does not encode culture.
- **Prompts** are deterministic. Tests freeze the Jante laws and the "keep the language" rule.
- **LLM** is a protocol + `MockLLMClient`. No hidden OpenAI import on the default path.
- **Result** tells you which axis moved (`language_changed`, `style_changed`) and what the model claims it preserved.

## Tests

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

## License

MIT
