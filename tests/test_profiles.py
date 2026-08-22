"""Shipped profiles are data, not code. Janteloven is the canonical example."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from kofte.profiles import bundled_profile, list_profiles, load_profile


def test_norwegian_jante_is_bundled():
    names = list_profiles()
    assert "norwegian_jante" in names
    assert "polish_direct" in names
    assert "american_english" in names


def test_norwegian_jante_treats_janteloven_and_egalitarianism_as_supreme():
    profile = bundled_profile("norwegian_jante")
    assert profile.id == "norwegian_jante"
    assert profile.language_hint == "nb"
    supreme = {axis.id for axis in profile.supreme}
    assert supreme == {"janteloven", "egalitarianism"}
    summary = profile.summary.lower()
    assert "not above" in summary
    rules = " ".join(profile.rules).lower()
    assert "we" in rules
    assert "special" in rules or "better than" in rules
    # The ten laws of Jante must be present as source material, not a parody.
    laws = "\n".join(profile.canon).lower()
    assert "smarter" in laws or "cleverer" in laws or "klokere" in laws
    assert len(profile.canon) >= 10


def test_polish_direct_treats_directness_and_productivity_as_supreme():
    profile = bundled_profile("polish_direct")
    supreme = {axis.id for axis in profile.supreme}
    assert supreme == {"directness", "productivity"}
    rules = " ".join(profile.rules).lower()
    assert "task" in rules or "fact" in rules
    assert "imperative" in rules or "short" in rules


def test_load_profile_from_folder(tmp_path: Path):
    folder = tmp_path / "quiet_brit"
    folder.mkdir()
    (folder / "profile.toml").write_text(
        """
id = "quiet_brit"
name = "Quiet British understatement"
language_hint = "en"
summary = "Understate, never boast, leave an exit."
supreme = ["understatement", "face"]

[[axes]]
id = "understatement"
name = "Understatement"
description = "Say less than you mean."

[[axes]]
id = "face"
name = "Face"
description = "Leave the other person a way out."
""".lstrip()
    )
    (folder / "rules.md").write_text("- Hedge.\n- Do not boast.\n")
    profile = load_profile(folder)
    assert profile.id == "quiet_brit"
    assert {a.id for a in profile.supreme} == {"understatement", "face"}
    assert any("Hedge" in r for r in profile.rules)


def test_unknown_bundled_profile_raises():
    with pytest.raises(KeyError):
        bundled_profile("does_not_exist")


def test_profile_is_frozen():
    profile = bundled_profile("norwegian_jante")
    with pytest.raises((ValidationError, TypeError)):
        profile.id = "mutated"  # type: ignore[misc]


def test_american_english_treats_agency_and_positivity_as_supreme():
    profile = bundled_profile("american_english")
    assert profile.id == "american_english"
    assert profile.language_hint == "en"
    supreme = {axis.id for axis in profile.supreme}
    assert supreme == {"agency", "positivity"}
    rules = " ".join(profile.rules).lower()
    assert "i " in rules or "owner" in rules or "next step" in rules
    anti = " ".join(profile.anti_patterns).lower()
    assert "hustle" in anti or "synergy" in anti or "fake" in anti
