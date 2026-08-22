"""Slack-shaped host: event + thread → Translator.

This is not a Slack app. It shows the seam a bot would call.
"""

from kofte import Translator, from_slack
from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft

llm = MockLLMClient(
    responses=[
        TranslationDraft(
            text="Something here does not work yet. We could look at it together.",
            language="en",
            style="norwegian_jante",
        )
    ]
)
engine = Translator(llm=llm)

event = {
    "type": "message",
    "text": "This is wrong. Fix it.",
    "user": "U1",
    "channel": "C1",
    "ts": "2",
}
thread = [
    {"user": "U9", "text": "Can you look at my PR?", "ts": "1"},
    event,
]
inbound = from_slack(event, thread=thread)
result = engine.translate(
    inbound.text,
    source="en+polish_direct",
    target="en+norwegian_jante",
    context=inbound.context,
)
print(result.text)
