"""Emitype-shaped host: traits in, rewritten message out.

Kofte does not import emitype. The host builds a Lens from traits.
"""

from kofte import Translator, lens_from_traits
from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft

listener = lens_from_traits(
    "emi:203412107403302401",
    "Listener",
    [
        ("Osobowość", "Kontraktowiec"),
        ("Faktor", "dynamika 4"),
        ("Stan umysłu", "emi3"),
    ],
    summary="Keep it concrete. Match the listener.",
)

llm = MockLLMClient(
    responses=[
        TranslationDraft(
            text="Możemy spojrzeć na to razem. Tu jeszcze coś nie działa.",
            language="pl",
            style="emi:203412107403302401",
        )
    ]
)
engine = Translator(llm=llm)
print(
    engine.translate(
        "To jest źle. Popraw to.",
        source="pl",
        target="pl",
        target_lens=listener,
    ).text
)
