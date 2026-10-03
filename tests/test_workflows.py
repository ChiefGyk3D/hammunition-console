# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import re
from pathlib import Path

import pytest

WORKFLOWS = sorted((Path(__file__).resolve().parent.parent / ".github" / "workflows").glob("*.yml"))
USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)@(\S+)(?:\s+#\s*(v\S+))?\s*$")
ENV_ASSIGN = re.compile(r"^\s+[A-Z][A-Z_]*:\s+\$\{\{[^}]+\}\}\s*$")
SAFE_KEYS = re.compile(r"^\s*(if|group|name|runs-on|python-version|cancel-in-progress|publish):")


def test_there_are_workflows() -> None:
    assert {w.name for w in WORKFLOWS} == {"ci.yml", "release.yml", "security.yml"}


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_action_is_pinned_to_a_resolved_commit_with_its_tag_in_a_comment(path: Path) -> None:
    uses = [USES.match(line) for line in path.read_text().splitlines() if "uses:" in line]
    assert uses, "no actions found"
    for m in uses:
        assert m, "an unparsable `uses:` line"
        assert re.fullmatch(r"[0-9a-f]{40}", m.group(2)), (
            f"{path.name}: {m.group(1)}@{m.group(2)} is not a commit; resolve it with `git ls-remote --tags` (see Task 18)")
        assert m.group(3), f"{path.name}: {m.group(1)} pin has no `# vX.Y.Z` tag comment"
    assert "PIN_" not in path.read_text()


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_a_tag_or_ref_never_reaches_shell_except_through_env(path: Path) -> None:
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if "${{" not in line:
            continue
        ok = ENV_ASSIGN.match(line) or SAFE_KEYS.match(line) or ("matrix." in line and "github." not in line)
        assert ok, f"{path.name}:{number}: an expression outside env/if/group/matrix: {line.strip()}"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_permissions_default_to_read_only(path: Path) -> None:
    assert re.search(r"^permissions:\n  contents: read$", path.read_text(), re.M)


GYST = "ChiefGyk3D/git-your-ship-together/.github/workflows/"
README = (Path(__file__).resolve().parent.parent / "README.md").read_text()


@pytest.mark.parametrize(
    ("name", "reusable"),
    [("ci.yml", ("python-ci.yml", "bash-ci.yml")), ("security.yml", ("security.yml",)),
     ("release.yml", ("artifact-release.yml",))],
)
def test_ci_security_and_release_call_the_shared_workflows(name: str, reusable: tuple[str, ...]) -> None:
    text = (WORKFLOWS[0].parent / name).read_text()
    for workflow in reusable:
        assert f"uses: {GYST}{workflow}@" in text, f"{name} does not call GYST's {workflow}"


def test_the_readme_lists_the_required_checks_the_workflows_produce() -> None:
    development = README.split("\n## Development\n")[1].split("\n## ")[0]
    for check in ("ci / CI green", "shell / CI green", "local jobs green"):
        assert f"`{check}`" in development, f"README's Development section does not list the required check {check}"
    ci = (WORKFLOWS[0].parent / "ci.yml").read_text()
    assert "name: local jobs green" in ci and "\n  ci:\n" in ci and "\n  shell:\n" in ci
