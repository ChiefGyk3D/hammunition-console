# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared test helpers. FakeEngine and FakeContext are added in later tasks."""

from __future__ import annotations

import json
import shlex
import stat
import sys
from pathlib import Path
from typing import Any

import urwid

FIXTURES = Path(__file__).parent / "fixtures"
FAKE = Path(__file__).parent / "fake_hammunition.py"


def load(name: str) -> dict[str, Any]:
    """A recorded fixture's document, by file stem."""
    data = json.loads((FIXTURES / f"{name}.json").read_text())
    assert isinstance(data, dict)
    return data


def make_shim(directory: Path) -> Path:
    """A directory holding an executable `hammunition` that runs the fake with this interpreter."""
    bin_dir = directory / "shim-bin"
    bin_dir.mkdir(exist_ok=True)
    shim = bin_dir / "hammunition"
    shim.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(FAKE))} \"$@\"\n")
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def render(widget: urwid.Widget, cols: int = 80, rows: int = 24) -> str:
    """A box widget drawn to text, trailing blanks trimmed."""
    canvas = widget.render((cols, rows), focus=True)
    return "\n".join(line.decode("utf-8").rstrip() for line in canvas.text)
