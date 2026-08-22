"""A host-built lens: traits in, rewritten message out. No profile folder."""

from kofte import Translator, lens_from_traits
from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft

reviewer = lens_from_traits(
    "brief_reviewer",
    "Brief reviewer",
    [
        ("Tone", "dry"),
        ("Length", "two sentences"),
        ("Always", "name the file"),
    ],
    summary="Short notes. Name the file and the next step.",
)

llm = MockLLMClient(
    responses=[
        TranslationDraft(
            text="parser.py still drops empty tags. Re-run the fixture.",
            language="en",
            style="brief_reviewer",
        )
    ]
)
engine = Translator(llm=llm)
print(
    engine.translate(
        "This is wrong. Fix it.",
        source="en",
        target="en",
        target_lens=reviewer,
    ).text
)
