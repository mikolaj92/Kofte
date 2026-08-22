"""Language and style are independent axes."""

from __future__ import annotations

import pytest

from kofte.registers import Register, parse_register


def test_register_keeps_language_and_style_apart():
    r = Register(language="en", style="norwegian_jante")
    assert r.language == "en"
    assert r.style == "norwegian_jante"
    assert r.changes_language(Register(language="en", style="polish_direct")) is False
    assert r.changes_style(Register(language="en", style="polish_direct")) is True


def test_register_normalizes_norwegian_codes():
    assert Register(language="no", style="norwegian_jante").language == "nb"
    assert Register(language="nb", style="norwegian_jante").language == "nb"
    assert Register(language="nn", style="norwegian_jante").language == "nn"


def test_parse_register_accepts_language_only():
    r = parse_register("pl")
    assert r.language == "pl"
    assert r.style is None


def test_parse_register_accepts_language_plus_style():
    r = parse_register("en+norwegian_jante")
    assert r.language == "en"
    assert r.style == "norwegian_jante"


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError, match="language"):
        Register(language="xx", style="norwegian_jante")


def test_register_allows_inferred_language():
    r = Register()
    assert r.language is None
    assert r.style is None
    assert r.changes_language(Register(language="en")) is True
    assert Register(language="und").language is None
    assert Register(language="auto").language is None


def test_parse_register_accepts_style_only():
    r = parse_register("kofte")
    assert r.language is None
    assert r.style == "kofte"
    assert parse_register("+kofte").style == "kofte"
    assert parse_register("auto").language is None
