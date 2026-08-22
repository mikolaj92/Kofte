"""Register a third style pack, then translate into it by id."""

from pathlib import Path

from kofte import Translator, load_profile
from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft

folder = Path(__file__).parent / "quiet_brit"
llm = MockLLMClient(
    responses=[TranslationDraft(text="Perhaps we revisit this.", language="en", style="quiet_brit")]
)
engine = Translator(llm=llm)
engine.registry.register(load_profile(folder))
out = engine.translate("This is wrong. Fix it.", source="en+polish_direct", target="en+quiet_brit")
print(out.text)
