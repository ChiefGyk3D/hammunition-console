#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""Add or check the two-line source header on every .py, .sh and bin/ file.

    python3 scripts/spdx.py --check   # exit 1 naming each file without it
    python3 scripts/spdx.py --fix     # prepend it (after a shebang) where missing
"""

from __future__ import annotations

import sys
from pathlib import Path

HEADER = [
    "# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC",
    "# SPDX-License-Identifier: GPL-3.0-or-later",
]
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "dist", ".mypy_cache", ".pytest_cache"}


def source_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS or not path.is_file():
            continue
        in_bin = path.relative_to(root).parts[:1] == ("bin",)
        if path.suffix in {".py", ".sh"} or in_bin:
            found.append(path)
    return found


def has_header(text: str) -> bool:
    lines = text.splitlines()
    body = lines[1:] if lines and lines[0].startswith("#!") else lines
    return body[:2] == HEADER


def add_header(text: str) -> str:
    if has_header(text):
        return text
    lines = text.splitlines()
    shebang = [lines.pop(0)] if lines and lines[0].startswith("#!") else []
    out = [*shebang, *HEADER, *lines]
    return "\n".join(out) + "\n"


def missing(root: Path) -> list[Path]:
    return [p for p in source_files(root) if not has_header(p.read_text(encoding="utf-8"))]


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    if argv == ["--fix"]:
        for path in missing(root):
            path.write_text(add_header(path.read_text(encoding="utf-8")), encoding="utf-8")
            print(f"added header: {path.relative_to(root)}")
        return 0
    if argv == ["--check"]:
        bad = missing(root)
        for path in bad:
            print(f"missing header: {path.relative_to(root)} (run: python3 scripts/spdx.py --fix)")
        return 1 if bad else 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
