# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.helpers import make_shim
from tests.pty_driver import PtyProcess

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.pty


def env_for(tmp: Path) -> dict[str, str]:
    return {
        "PATH": f"{make_shim(tmp)}:{os.environ['PATH']}",
        "HOME": str(tmp), "TERM": "xterm-256color", "LANG": "C.UTF-8",
        "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1",
        "FAKE_HAMMUNITION_LOG": str(tmp / "fake.log"), "HARNESS_RESULT": str(tmp / "result"),
        "HAMMUNITION_ACCEPT_RF_RESEARCH": "1",  # a canary: it must not reach the child
    }


def harness(env: dict[str, str]) -> PtyProcess:
    return PtyProcess([sys.executable, "-m", "tests.pane_harness", "--", "hammunition", "install", "station"], env)


def test_a_person_typing_yes_into_a_real_tty_is_what_confirms(tmp_path: Path) -> None:
    env = env_for(tmp_path)
    proc = harness(env)
    try:
        proc.expect("continue:")
        proc.send("yes\r")
        proc.expect("Finished with exit code 0")
        proc.send("\r")
        assert proc.wait() == 0
    finally:
        proc.close()
    assert (tmp_path / "result").read_text().strip() == "0"
    entry = json.loads((tmp_path / "fake.log").read_text().splitlines()[0])
    assert entry["argv"] == ["install", "station"] and entry["tty"] is True
    assert "HAMMUNITION_ACCEPT_RF_RESEARCH" not in entry["env"], "the consent variable leaked into the pane's child"


def test_anything_but_yes_is_declined_and_the_exit_code_is_the_engines(tmp_path: Path) -> None:
    env = env_for(tmp_path)
    proc = harness(env)
    try:
        proc.expect("continue:")
        proc.send("no\r")
        proc.expect("Finished with exit code 3")
        proc.send("\r")
        proc.wait()
    finally:
        proc.close()
    assert (tmp_path / "result").read_text().strip() == "3"


def test_the_same_fake_refuses_without_a_tty_so_the_tty_above_was_real(tmp_path: Path) -> None:
    shim = make_shim(tmp_path)
    done = subprocess.run(["hammunition", "install", "station"], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, env={**os.environ, "PATH": f"{shim}:{os.environ['PATH']}"})
    assert done.returncode == 3 and "no interactive terminal" in done.stderr
