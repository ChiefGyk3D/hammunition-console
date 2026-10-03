# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

import pytest

from hammunition_console.app import SCREEN_CLASSES, build_registry
from hammunition_console.helptext import EXIT_CODES, KEYS
from tests.helpers import FakeContext

ROOT = Path(__file__).resolve().parent.parent
MAN = (ROOT / "man" / "hammunition-console.1").read_text().replace("\\-", "-").replace("\\fB", "").replace("\\fR", "").replace("\\fI", "")


def test_the_man_page_documents_every_key_every_exit_code_and_the_config_file() -> None:
    for keys, _ in KEYS:
        assert keys in MAN, f"man page lacks key {keys!r}"
    for code, _ in EXIT_CODES:
        assert f"\n{code}\n" in MAN or f" {code} " in MAN or f"{code}  " in MAN, f"exit code {code}"
    assert "config.toml" in MAN and "crash.log" in MAN and ".TH HAMMUNITION-CONSOLE 1" in MAN


def test_the_man_page_names_what_it_never_does() -> None:
    assert "never" in MAN.lower() and "consent" in MAN.lower()


@pytest.mark.parametrize("name", sorted(SCREEN_CLASSES))
def test_every_registered_screen_resolves_and_builds(name: str) -> None:
    screen = build_registry()[name](FakeContext())
    assert screen.name == name
