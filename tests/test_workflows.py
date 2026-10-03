# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import re
from pathlib import Path

import pytest

WORKFLOWS = sorted((Path(__file__).resolve().parent.parent / ".github" / "workflows").glob("*.yml"))
USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)@(\S+)(?:\s+#\s*(v\S+))?\s*$")
ENV_ASSIGN = re.compile(r"^\s+[A-Z][A-Z_]*:\s+\$\{\{[^}]+\}\}\s*$")
SAFE_KEYS = re.compile(r"^\s*(if|group|name|runs-on|python-version|cancel-in-progress):")


def test_there_are_workflows() -> None:
    assert {w.name for w in WORKFLOWS} == {"ci.yml", "release.yml"}


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
