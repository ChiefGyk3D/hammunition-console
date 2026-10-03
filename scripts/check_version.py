#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""Refuse a release tag that disagrees with the tree it points at.

The tag is the one release input a human types. A v0.2.0 tag on a package that says
0.1.0 publishes a version number that means two things."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def check(tag: str, root: Path) -> str:
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError(f"tag {tag!r} is not vMAJOR.MINOR.PATCH")
    wanted = tag[1:]
    init = (root / "hammunition_console" / "__init__.py").read_text()
    match = re.search(r'^__version__ = "([^"]+)"', init, re.M)
    have = match.group(1) if match else "(none)"
    if have != wanted:
        raise ValueError(f"tag {tag} but __version__ says {have}")
    changelog = (root / "CHANGELOG.md").read_text()
    if not re.search(rf"^## v{re.escape(wanted)}\b", changelog, re.M):
        raise ValueError(f"CHANGELOG.md has no '## v{wanted}' section (run scripts/changelog.py assemble)")
    man = (root / "man" / "hammunition-console.1").read_text()
    if f'"hammunition-console {wanted}"' not in man:
        raise ValueError(f"man/hammunition-console.1 does not say {wanted} in its .TH line")
    return wanted


if __name__ == "__main__":
    try:
        print(check(sys.argv[1], Path(__file__).resolve().parent.parent))
    except (IndexError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
