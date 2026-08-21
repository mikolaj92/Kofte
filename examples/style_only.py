"""Style-only rewrite: English stays English, register becomes Jante."""

from kofte import MockLLMClient, TranslationDraft, translate

llm = MockLLMClient(
    responses=[
        TranslationDraft(
            text="Something here does not work yet. We could look at it again together.",
            language="en",
            style="norwegian_jante",
            moves=["we", "yet"],
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
print("language_changed", result.language_changed)
print("style_changed", result.style_changed)
