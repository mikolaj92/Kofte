"""CLI: list profiles, print a prompt, translate with an injected mock."""

from __future__ import annotations

from kofte.cli import main


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
