# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""Text the console shows and prints. Keep the literal consent tokens out of here:
tests/test_consent_guard.py fails if one appears anywhere in the package but guard.py."""

from __future__ import annotations

USAGE = """\
usage: hammunition-console [--help] [--version]

A full-screen terminal front end for the Hammunition engine. It reads the
engine's JSON documents and runs the engine's own commands in a terminal pane;
it never answers a consent prompt for you. Needs a terminal at least 80x24."""

# (keys, meaning). Every key listed here is handled somewhere; the README's
# keys table is generated from this tuple's content by hand and a test checks it.
KEYS: tuple[tuple[str, str], ...] = (
    ("1-5", "open the screen with that number (Home)"),
    ("Enter", "open the selected row"),
    ("b / Esc", "go back; changes nothing"),
    ("?", "help"),
    ("q", "quit"),
    ("r", "refresh this screen"),
    ("R", "run the planned command in a terminal pane (plan and confirm screens)"),
    ("Tab", "switch between profiles and single units (Install)"),
    ("U", "plan an uninstall of the selected profile (Install)"),
    ("i", "the selected profile's documentation (Install)"),
    ("v", "reveal or hide station values (Station)"),
    ("c", "clear the selected value, where the engine can (Station)"),
    ("u", "also ask upstream whether the catalog's pins are current (Update)"),
    ("A", "run the apt upgrade the report offers (Update)"),
    ("B", "plan the rebuilds the report offers (Update)"),
    ("s", "skip the selected first-run step (Home)"),
    ("D", "dismiss the first-run checklist (Home)"),
)

EXIT_CODES = (
    ("0", "normal exit"),
    ("1", "the console crashed (details, without any message text, in crash.log)"),
    ("2", "the console refused to start: no terminal, TERM=dumb, running as root, bad argument"),
)


def full_help() -> str:
    lines = [USAGE, "", "Keys:"]
    lines += [f"  {keys:<10} {meaning}" for keys, meaning in KEYS]
    lines += ["", "Exit codes:"]
    lines += [f"  {code:<10} {meaning}" for code, meaning in EXIT_CODES]
    return "\n".join(lines)
