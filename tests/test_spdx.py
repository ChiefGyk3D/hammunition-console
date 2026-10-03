# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

from scripts import spdx

ROOT = Path(__file__).resolve().parent.parent


def test_every_source_file_has_the_header() -> None:
    assert spdx.missing(ROOT) == [], "run: python3 scripts/spdx.py --fix"


def test_add_header_is_idempotent_and_keeps_the_shebang() -> None:
    once = spdx.add_header("#!/bin/sh\necho hi\n")
    assert once.splitlines()[:3] == ["#!/bin/sh", *spdx.HEADER]
    assert spdx.add_header(once) == once


def test_add_header_without_a_shebang() -> None:
    text = spdx.add_header("x = 1\n")
    assert text.splitlines()[:2] == spdx.HEADER and text.endswith("x = 1\n")


def test_check_detects_a_file_without_it(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    assert [p.name for p in spdx.missing(tmp_path)] == ["a.py"]
