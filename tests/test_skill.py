"""The engine ships as an agent skill, not only as a Python import."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "kofte" / "SKILL.md"


def test_skill_file_exists_with_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: kofte" in text
    assert "description:" in text
    body = text.split("---", 2)[2]
    assert "kofte mcp" in body.lower() or "kofte-mcp" in body.lower()
    assert "translate" in body.lower()
    assert "pl" in body and "en" in body
    assert "en+kofte" in body or "hops" in body.lower()
