# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "changelog.py"


def load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("changelog_script", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["changelog_script"] = module
    spec.loader.exec_module(module)
    return module


def tree(tmp_path: Path, changelog: str) -> Path:
    (tmp_path / "changelog.d").mkdir()
    (tmp_path / "changelog.d" / "x.added.md").write_text("- Added a thing.\n")
    (tmp_path / "CHANGELOG.md").write_text(changelog)
    return tmp_path


def test_a_first_release_can_be_assembled_from_an_unreleased_only_changelog(tmp_path: Path) -> None:
    root = tree(tmp_path, "# Changelog\n\n## Unreleased\n\nNothing yet.\n")
    done = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "assemble", "--version", "v0.1.0", "--date", "2026-10-03"],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    text = (root / "CHANGELOG.md").read_text()
    assert "## Unreleased\n\nNothing yet." in text and "## v0.1.0 — 2026-10-03" in text and "- Added a thing." in text
    assert not (root / "changelog.d" / "x.added.md").exists()


def test_the_real_changelog_says_nothing_yet_until_a_release_is_cut() -> None:
    assert "## Unreleased\n\nNothing yet." in (ROOT / "CHANGELOG.md").read_text()


def test_the_real_tree_previews_with_or_without_fragments() -> None:
    # after `assemble` deletes the fragments the preview must still exit 0 on the release commit
    done = subprocess.run([sys.executable, str(SCRIPT), "preview"], capture_output=True, text=True, cwd=ROOT)
    assert done.returncode == 0, done.stderr


def test_a_fixture_fragment_previews_its_text(tmp_path: Path) -> None:
    root = tree(tmp_path, "# Changelog\n\n## Unreleased\n\nNothing yet.\n")
    done = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "preview"], capture_output=True, text=True)
    assert done.returncode == 0 and "Added a thing." in done.stdout, done.stderr


def test_a_pull_request_that_changes_the_package_needs_a_fragment() -> None:
    mod = load()
    assert mod.pr_problem(["hammunition_console/app.py"], [], []) is not None
    assert mod.pr_problem(["hammunition_console/app.py", "changelog.d/9.fixed.md"], ["changelog.d/9.fixed.md"], []) is None
    assert mod.pr_problem(["README.md"], [], []) is None
