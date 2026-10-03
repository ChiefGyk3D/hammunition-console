# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from hammunition_console.pane import RUNNER


def run_runner(status: Path, *command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(RUNNER), str(status), "--", *command],
                          capture_output=True, text=True, stdin=subprocess.DEVNULL)


def test_it_reports_the_childs_exit_code_in_the_file_and_as_its_own(tmp_path: Path) -> None:
    status = tmp_path / "status"
    done = run_runner(status, sys.executable, "-c", "import sys; sys.exit(7)")
    assert done.returncode == 7 and status.read_text().strip() == "7"


def test_a_missing_command_is_127(tmp_path: Path) -> None:
    status = tmp_path / "status"
    done = run_runner(status, "no-such-command-xyz")
    assert done.returncode == 127 and status.read_text().strip() == "127"
    assert "not found" in done.stderr


def test_usage_error_is_2(tmp_path: Path) -> None:
    done = subprocess.run([sys.executable, str(RUNNER), str(tmp_path / "s")], capture_output=True, text=True)
    assert done.returncode == 2


def test_ctrl_c_reaches_the_child_and_does_not_kill_the_runner(tmp_path: Path) -> None:
    """SIGINT goes to the whole foreground group, as a terminal's Ctrl-C does. The runner must
    ignore it (its handler is a no-op) and report what the child did with it."""
    status = tmp_path / "status"
    child = ("import signal, sys, time\n"
             "signal.signal(signal.SIGINT, lambda *a: sys.exit(5))\n"
             "print('ready', flush=True)\n"
             "time.sleep(30)\n")
    proc = subprocess.Popen([sys.executable, str(RUNNER), str(status), "--", sys.executable, "-c", child],
                            stdout=subprocess.PIPE, text=True, start_new_session=True)
    assert proc.stdout is not None
    try:
        assert proc.stdout.readline().strip() == "ready"
        os.killpg(proc.pid, signal.SIGINT)
        deadline = time.monotonic() + 10
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert proc.poll() == 5 and status.read_text().strip() == "5"
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        proc.stdout.close()


def test_a_child_killed_by_a_signal_is_reported_as_128_plus_the_signal(tmp_path: Path) -> None:
    status = tmp_path / "status"
    done = run_runner(status, sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)")
    assert done.returncode == 128 + signal.SIGTERM
