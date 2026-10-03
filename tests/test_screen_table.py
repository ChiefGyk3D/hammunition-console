# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""The spec: a command with no JSON form returns an error document, ran nothing, and is a bug in the
screen table. Two checks: statically, every literal verb in the package is a JSON verb; dynamically,
driving every screen reads exactly the verbs below, so a new read cannot slip in unseen."""

import re
from pathlib import Path

from hammunition_console.screens.help import HelpScreen, ProfileDocsScreen
from hammunition_console.screens.home import HomeScreen
from hammunition_console.screens.install import InstallScreen
from hammunition_console.screens.logs import LogsScreen
from hammunition_console.screens.plan import PlanScreen
from hammunition_console.screens.station import StationScreen
from hammunition_console.screens.update import UpdateScreen
from hammunition_console.verbs import JSON_VERBS, verb_of
from tests.helpers import FakeContext, FakeEngine

PACKAGE = Path(__file__).resolve().parent.parent / "hammunition_console"
READ = re.compile(r"engine\.read\(\s*\"([a-z-]+)\"(?:\s*,\s*\"([a-z-]+)\")?")
EXPECTED = {("status",), ("doctor",), ("list",), ("show",), ("logs",), ("update",), ("station", "show"),
            ("install",), ("uninstall",), ("maps", "regions"), ("reference", "books")}


def test_every_literal_read_in_the_package_is_a_json_verb() -> None:
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        for m in READ.finditer(path.read_text()):
            words = tuple(w for w in m.groups() if w)
            found.append((path.name, words))
            assert verb_of(words) in JSON_VERBS, f"{path.name}: {words} has no --json form"
    assert len(found) >= 8, "the scan found too few reads to mean anything"


def test_driving_every_screen_reads_exactly_the_expected_verbs() -> None:
    ctx = FakeContext()
    for screen in (HomeScreen(ctx), InstallScreen(ctx), StationScreen(ctx), LogsScreen(ctx), UpdateScreen(ctx),
                   UpdateScreen(ctx, names=["station"]), HelpScreen(ctx), ProfileDocsScreen(ctx, "station"),
                   PlanScreen(ctx, "install", ["station"]), PlanScreen(ctx, "uninstall", ["station"])):
        screen.on_show()
    station = StationScreen(ctx)
    station.on_show()
    station._choose_books()
    ctx.pushed[-1].on_show()
    station._search_regions("vermont")
    ctx.pushed[-1].on_show()
    engine: FakeEngine = ctx.engine
    assert {verb_of(call) for call in engine.calls} == EXPECTED
    assert EXPECTED <= JSON_VERBS
