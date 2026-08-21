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
    monkeypatch.setattr("kofte.cli.build_llm", lambda: llm)
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
    monkeypatch.setattr("kofte.cli.build_llm", lambda: llm)
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
    monkeypatch.setattr("kofte.cli.build_llm", lambda: None)
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
