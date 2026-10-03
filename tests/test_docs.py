# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

from hammunition_console.config import SCREENS
from hammunition_console.engine import ENGINE_FLOOR
from hammunition_console.helptext import KEYS, NEVER
from hammunition_console.verbs import JSON_VERBS
from tests.fixture_scan import findings

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text()
CONTRACT = (ROOT / "docs" / "contract.md").read_text()


def test_the_readme_has_every_required_section() -> None:
    for heading in ("What it is", "Requirements", "Install", "How it works", "What it never does", "Keys", "Screens",
                    "Status", "Development", "Licence"):
        assert f"\n## {heading}\n" in README, heading


def test_the_keys_table_lists_every_key_in_the_help() -> None:
    for keys, meaning in KEYS:
        assert f"| `{keys}` | {meaning} |" in README, f"README keys table is out of step with helptext.KEYS: {keys}"


def test_the_readme_names_every_screen_and_counts_them_right() -> None:
    assert "six screens" in README.lower() and len(SCREENS) == 6
    for screen in SCREENS:
        assert f"**{screen.capitalize()}**" in README, screen


def test_the_never_section_carries_the_help_text_verbatim() -> None:
    never = README.split("\n## What it never does\n")[1].split("\n## ")[0]
    for line in NEVER:
        assert f"- {line}" in never, f"README is out of step with helptext.NEVER: {line}"


def test_the_readme_states_the_engine_floor() -> None:
    assert ".".join(str(n) for n in ENGINE_FLOOR) in README


def test_the_status_section_says_what_has_not_run_on_real_hardware() -> None:
    status = README.split("\n## Status\n")[1].split("\n## ")[0]
    assert "has not been run" in status and "real target" in status and "urwid.Terminal" in status


def test_the_readme_and_contract_carry_no_identifier() -> None:
    assert findings(README) == [] and findings(CONTRACT) == []


def test_the_contract_lists_every_verb_the_console_reads_and_both_engine_prerequisites() -> None:
    for verb in JSON_VERBS:
        assert f"`hammunition {' '.join(verb)}" in CONTRACT, verb
    assert "E1" in CONTRACT and "E2" in CONTRACT and "unknown" in CONTRACT


def test_the_readme_says_how_the_three_channels_differ() -> None:
    assert "worker thread" in README and "terminal pane" in README and "config.toml" in README
