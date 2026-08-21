"""Host adapters: Slack event, clipboard, generic inbound message."""

from __future__ import annotations

from kofte.hosts import InboundMessage, from_browser, from_clipboard, from_slack, translate_inbound


def test_from_slack_extracts_text_and_thread_context():
    event = {
        "type": "message",
        "text": "This is wrong. Fix it.",
        "user": "U123",
        "channel": "C99",
        "thread_ts": "1.0",
        "ts": "1.1",
    }
    thread = [
        {"user": "U1", "text": "Can you look at my PR?", "bot_id": None},
        {"user": "U2", "text": "Sure.", "bot_id": "B1"},
        event,
    ]
    inbound = from_slack(event, thread=thread)
    assert inbound.text == "This is wrong. Fix it."
    assert inbound.source_id == "slack:C99:1.1"
    roles = [(t.role, t.text) for t in inbound.context]
    assert ("user", "Can you look at my PR?") in roles
    assert ("assistant", "Sure.") in roles
    assert inbound.text not in [t.text for t in inbound.context]


def test_from_clipboard_is_plain_text():
    inbound = from_clipboard("This is wrong. Fix it.")
    assert inbound.text == "This is wrong. Fix it."
    assert inbound.context == ()
    assert inbound.host == "clipboard"


def test_inbound_message_is_the_generic_host_shape():
    msg = InboundMessage(text="hi", host="browser", source_id="ext:1")
    assert msg.text == "hi"


def test_from_browser_uses_selection_and_url():
    inbound = from_browser(
        {
            "selection": "This is wrong. Fix it.",
            "page_url": "https://github.com/x/y/pull/1",
            "context": [{"role": "user", "text": "please review"}],
        }
    )
    assert inbound.text == "This is wrong. Fix it."
    assert inbound.host == "browser"
    assert "github.com" in (inbound.source_id or "")
    assert inbound.context[0].text == "please review"



def test_translate_inbound_forwards_context():
    from kofte import Translator
    from kofte.llm import MockLLMClient
    from kofte.models import TranslationDraft

    llm = MockLLMClient(
        responses=[TranslationDraft(text="we look", language="en", style="norwegian_jante")]
    )
    inbound = from_slack(
        {"text": "This is wrong.", "user": "U1", "channel": "C1", "ts": "2"},
        thread=[{"user": "U9", "text": "please review", "ts": "1"}],
    )
    result = translate_inbound(
        Translator(llm=llm),
        inbound,
        "en+polish_direct",
        "en+norwegian_jante",
    )
    blob = "\n".join(m["content"] for m in llm.calls[0].messages)
    assert "please review" in blob
    assert result.text == "we look"
