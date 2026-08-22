"""Compose: Polish → English, then English → English Kofte (Norwegian voice)."""

from kofte import MockLLMClient, TranslationDraft, translate

llm = MockLLMClient(
    responses=[
        TranslationDraft(text="This is wrong. Fix it.", language="en", style=None),
        TranslationDraft(
            text="Something here does not work yet. We could look at it again together.",
            language="en",
            style="kofte",
            moves=["we", "yet"],
            preserved=["does not work"],
        ),
    ]
)

result = translate(
    "To jest źle. Popraw to.",
    hops=["pl", "en", "en+kofte"],
    llm=llm,
)
print(result.text)
print("source", result.source)
print("target", result.target)
