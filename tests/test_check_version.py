# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

import pytest

from hammunition_console import __version__
from scripts.check_version import check

ROOT = Path(__file__).resolve().parent.parent


def tree(tmp_path: Path, version: str = "0.2.0", section: str = "v0.2.0", man: str = "0.2.0") -> Path:
    (tmp_path / "hammunition_console").mkdir()
    (tmp_path / "hammunition_console" / "__init__.py").write_text(f'__version__ = "{version}"\n')
    (tmp_path / "CHANGELOG.md").write_text(f"## Unreleased\n\nNothing yet.\n\n## {section} — 2026-10-03\n\n- x\n")
    (tmp_path / "man").mkdir()
    (tmp_path / "man" / "hammunition-console.1").write_text(f'.TH HAMMUNITION-CONSOLE 1 "d" "hammunition-console {man}" "H"\n')
    return tmp_path


def test_a_tag_that_agrees_passes(tmp_path: Path) -> None:
    assert check("v0.2.0", tree(tmp_path)) == "0.2.0"


@pytest.mark.parametrize("tag", ["0.2.0", "v0.2", "v0.2.0-rc1", "main"])
def test_a_malformed_tag_is_refused(tag: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
        check(tag, tree(tmp_path))


@pytest.mark.parametrize("kw,needle", [({"version": "0.1.9"}, "__version__"), ({"section": "v0.1.0"}, "CHANGELOG"), ({"man": "0.1.0"}, "man/")])
def test_each_disagreement_is_named(kw: dict[str, str], needle: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=needle):
        check("v0.2.0", tree(tmp_path, **kw))


def test_the_man_page_and_the_package_agree_today() -> None:
    assert f'"hammunition-console {__version__}"' in (ROOT / "man" / "hammunition-console.1").read_text()
