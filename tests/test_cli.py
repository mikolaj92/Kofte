"""CLI: list profiles, print a prompt, translate through an injected LLM."""

from __future__ import annotations

import json

from kofte.cli import main
from kofte.llm import MockLLMClient
from kofte.models import TranslationDraft


def test_cli_lists_bundled_profiles(capsys):
    code = main(["profiles"])
    captured = capsys.readouterr().out
    assert code == 0
    assert "norwegian_jante" in captured
    assert "polish_direct" in captured
    assert "american_english" in captured


def test_cli_prompt_prints_system_and_user(capsys):
    code = main(
        [
            "prompt",
            "--source",
            "en+polish_direct",
            "--target",
            "en+norwegian_jante",
            "This is wrong. Fix it.",
        ]
    )
    captured = capsys.readouterr().out.lower()
    assert code == 0
    assert "jante" in captured
    assert "this is wrong" in captured


def test_cli_translate_uses_injected_llm(capsys, monkeypatch):
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="Something here does not work yet.",
                language="en",
                style="norwegian_jante",
            )
        ]
    )
    monkeypatch.setattr("kofte.cli.build_llm", lambda **kwargs: llm)
    code = main(
        [
            "translate",
            "--source",
            "en+polish_direct",
            "--target",
            "en+norwegian_jante",
            "This is wrong. Fix it.",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "does not work yet" in captured.out


def test_cli_translate_json(capsys, monkeypatch):
    llm = MockLLMClient(
        responses=[
            TranslationDraft(
                text="We look again.",
                language="en",
                style="norwegian_jante",
                moves=["we"],
                preserved=["look"],
            )
        ]
    )
    monkeypatch.setattr("kofte.cli.build_llm", lambda **kwargs: llm)
    code = main(
        [
            "translate",
            "--json",
            "--source",
            "en+polish_direct",
            "--target",
            "en+norwegian_jante",
            "This is wrong.",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["text"] == "We look again."
    assert payload["style_changed"] is True


def test_cli_translate_without_llm_is_clear(capsys, monkeypatch):
    monkeypatch.setattr("kofte.cli.build_llm", lambda **kwargs: None)
    code = main(
        [
            "translate",
            "--source",
            "en+polish_direct",
            "--target",
            "en+norwegian_jante",
            "This is wrong.",
        ]
    )
    err = capsys.readouterr().err.lower()
    assert code == 2
    assert "llm" in err



def test_cli_translate_passes_base_url_and_model(capsys, monkeypatch):
    llm = MockLLMClient(
        responses=[
            TranslationDraft(text="we look", language="en", style="norwegian_jante")
        ]
    )
    seen: dict = {}

    def fake_build(base_url=None, model=None, api_key=None):
        seen["base_url"] = base_url
        seen["model"] = model
        seen["api_key"] = api_key
        return llm

    monkeypatch.setattr("kofte.cli.build_llm", fake_build)
    code = main(
        [
            "translate",
            "--base-url",
            "http://127.0.0.1:1234/v1",
            "--model",
            "qwen",
            "--source",
            "en+polish_direct",
            "--target",
            "en+norwegian_jante",
            "This is wrong.",
        ]
    )
    assert code == 0
    assert seen["base_url"] == "http://127.0.0.1:1234/v1"
    assert seen["model"] == "qwen"
    assert seen["api_key"] is None
    assert "we look" in capsys.readouterr().out


def test_cli_missing_llm_mentions_base_url_not_openai_key(capsys, monkeypatch):
    monkeypatch.setattr("kofte.cli.build_llm", lambda **kwargs: None)
    code = main(
        [
            "translate",
            "--source",
            "en+polish_direct",
            "--target",
            "en+norwegian_jante",
            "This is wrong.",
        ]
    )
    err = capsys.readouterr().err.lower()
    assert code == 2
    assert "base-url" in err
    assert "openai_api_key" not in err


def test_cli_translate_language_only(capsys, monkeypatch):
    llm = MockLLMClient(
        responses=[TranslationDraft(text="This is wrong.", language="en", style=None)]
    )
    monkeypatch.setattr("kofte.cli.build_llm", lambda **kwargs: llm)
    code = main(
        ["translate", "--source", "pl", "--target", "en", "To jest źle."]
    )
    assert code == 0
    assert "This is wrong." in capsys.readouterr().out


def test_cli_translate_target_form(capsys, monkeypatch):
    llm = MockLLMClient(
        responses=[TranslationDraft(text="ok", language="en", style=None)]
    )
    monkeypatch.setattr("kofte.cli.build_llm", lambda **kwargs: llm)
    code = main(
        [
            "translate",
            "--source",
            "en",
            "--target",
            "en",
            "--target-form",
            "Brief reviewer. Name the file.",
            "This is wrong. Fix it.",
        ]
    )
    assert code == 0
    assert "ok" in capsys.readouterr().out
    assert "Brief reviewer" in llm.calls[0].messages[0]["content"]
