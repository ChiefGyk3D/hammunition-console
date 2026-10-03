# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""The join Task 6 left untested: Shell.run_pane -> a factory built as app.run builds it -> the real PaneScreen."""

import os
import shutil
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

import pytest
import urwid

from hammunition_console.app import Shell
from hammunition_console.config import Config
from hammunition_console.guard import Refused
from hammunition_console.pane import PaneScreen
from hammunition_console.screens.base import Screen
from hammunition_console.worker import SyncBackground
from tests.helpers import FakeEngine, make_shim


@pytest.fixture
def shell(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Shell]:
    monkeypatch.setenv("PATH", f"{make_shim(tmp_path)}:{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_HAMMUNITION_LOG", str(tmp_path / "fake.log"))
    loop = urwid.MainLoop(urwid.SolidFill(" "))
    environ = {"PATH": os.environ["PATH"], "TERM": "xterm", "FAKE_HAMMUNITION_LOG": str(tmp_path / "fake.log"),
               "HAMMUNITION_ACCEPT_RF_RESEARCH": "1"}

    def factory(argv: Sequence[str], title: str, on_exit: Callable[[int | None], None]) -> Screen:
        return PaneScreen(sh, argv, title, on_exit, loop=loop, environ=environ)

    sh = Shell(FakeEngine(), Config(), SyncBackground(), pane_factory=factory, after=lambda s, f: None)
    yield sh
    for screen in sh.stack:
        if isinstance(screen, PaneScreen):
            screen.on_hangup()
            shutil.rmtree(screen._dir, ignore_errors=True)


def test_run_pane_pushes_a_real_pane_and_its_exit_reaches_the_callback(shell: Shell) -> None:
    exits: list[int | None] = []
    shell.run_pane(["hammunition", "install", "station"], "Install station", exits.append)
    pane = shell.stack[-1]
    assert isinstance(pane, PaneScreen) and pane.title == "Install station" and not pane.finished
    pane.finish()
    assert exits == [None]


def test_a_refused_command_never_becomes_a_pane(shell: Shell) -> None:
    with pytest.raises(Refused):
        shell.run_pane(["hammunition", "install", "station", "--yes"], "x", lambda code: None)
    assert shell.stack == []


def test_hangup_before_the_first_render_is_harmless(shell: Shell) -> None:
    shell.run_pane(["hammunition", "install", "station"], "x", lambda code: None)
    pane = shell.stack[-1]
    assert isinstance(pane, PaneScreen)
    pane.on_hangup()  # urwid forks the child on first render: nothing to end yet


def test_hangup_ends_a_running_child(shell: Shell) -> None:
    shell.run_pane(["hammunition", "install", "station"], "x", lambda code: None)
    pane = shell.stack[-1]
    assert isinstance(pane, PaneScreen)
    pane.widget().render((100, 30), focus=False)  # first render forks the child, waiting at the prompt
    pid = pane._terminal.pid
    assert isinstance(pid, int) and pid > 0
    pane.on_hangup()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            done, _ = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            break  # already reaped by urwid
        if done:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("the pane's child survived on_hangup")
