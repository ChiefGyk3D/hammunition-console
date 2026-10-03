# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import re
from pathlib import Path

import pytest

from hammunition_console import verbs
from hammunition_console.verbs import NotAJsonVerb

ENGINE_DOC = Path("/home/chiefgyk3d/src/Hammunition/docs/reference/json-interface.md")


@pytest.mark.parametrize("words,expected", [
    (["status"], ("status",)), (["station", "show"], ("station", "show")),
    (["maps", "regions", "vermont"], ("maps", "regions")), (["reference", "books"], ("reference", "books")),
    (["list", "profiles"], ("list",)), (["install", "x", "--dry-run"], ("install",)),
])
def test_verb_of(words: list[str], expected: tuple[str, ...]) -> None:
    assert verbs.verb_of(words) == expected


@pytest.mark.parametrize("words", [["hardware", "list"], ["station", "set", "--callsign=X"], ["time"],
                                   ["menus", "apply"], ["hardware", "apply"], []])
def test_a_verb_with_no_json_form_is_refused(words: list[str]) -> None:
    with pytest.raises(NotAJsonVerb):
        verbs.require_json_verb(words)


@pytest.mark.parametrize("verb", ["install", "uninstall"])
def test_install_and_uninstall_are_only_ever_read_as_a_dry_run(verb: str) -> None:
    with pytest.raises(NotAJsonVerb, match="dry-run"):
        verbs.require_json_verb([verb, "station"])
    verbs.require_json_verb([verb, "station", "--dry-run"])


def test_every_verb_is_one_the_engine_lists_under_commands() -> None:
    """The authority is the engine's own list. Skipped only where that checkout is absent."""
    if not ENGINE_DOC.exists():
        pytest.skip("engine checkout not present")
    text = ENGINE_DOC.read_text()
    listed = {tuple(m.group(1).split()) for m in re.finditer(r"^- `hammunition ([a-z ]+?)`", text, re.M)}
    for verb in verbs.JSON_VERBS:
        assert verb in listed, f"{verb} is not under Commands in json-interface.md: it has no JSON form"
