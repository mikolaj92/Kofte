"""Two public routes: Polish → American English, Polish → English Jante."""

from kofte import MockLLMClient, TranslationDraft, translate

american = MockLLMClient(
    responses=[
        TranslationDraft(
            text="This isn't landing yet. I'd take another pass on the null check.",
            language="en",
            style="american_english",
            moves=["agency"],
            preserved=["null"],
        )
    ]
)
jante = MockLLMClient(
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

src = "To jest źle. Popraw to."
a = translate(src, source="pl+polish_direct", target="en+american_english", llm=american)
j = translate(src, source="pl+polish_direct", target="en+norwegian_jante", llm=jante)
print("american:", a.text)
print("jante:   ", j.text)
