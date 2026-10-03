# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""An embedded terminal that runs the real engine command, so sudo's password
prompt, the group choice and any consent `yes` reach the engine untouched, typed
by a person. The console does not read the pane's input, echo it or inject keys."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import urwid

from hammunition_console import guard
from hammunition_console.context import Context
from hammunition_console.screens.base import Screen

RUNNER = Path(__file__).with_name("runner.py")


@dataclass(frozen=True)
class PaneSpec:
    command: list[str]
    env: dict[str, str]


def build_pane_spec(argv: Sequence[str], status_path: str, environ: Mapping[str, str]) -> PaneSpec:
    checked = guard.checked_argv(argv)
    env = guard.scrubbed_environ(environ)
    env.setdefault("TERM", "xterm-256color")
    return PaneSpec([sys.executable, str(RUNNER), status_path, "--", *checked], env)


def read_exit_status(path: str) -> int | None:
    try:
        return int(Path(path).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


class _PaneFrame(urwid.WidgetWrap):
    """All keys go to the program until it exits; then Enter continues."""

    def __init__(self, owner: PaneScreen, inner: urwid.Widget) -> None:
        self._owner = owner
        super().__init__(inner)

    def keypress(self, size: Any, key: str) -> str | None:
        if self._owner.finished:
            if key == "enter":
                self._owner.finish()
                return None
            return key
        return super().keypress(size, key)  # type: ignore[no-any-return]


class PaneScreen(Screen):
    name = "pane"

    def __init__(
        self,
        ctx: Context,
        argv: Sequence[str],
        title: str,
        on_exit: Callable[[int | None], None],
        *,
        loop: urwid.MainLoop,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(ctx)
        self.title = title
        self.finished = False
        self.exit_code: int | None = None
        self._on_exit = on_exit
        self._dir = tempfile.mkdtemp(prefix="hammunition-console-")
        self._status = os.path.join(self._dir, "status")
        spec = build_pane_spec(argv, self._status, os.environ if environ is None else environ)
        self._banner = urwid.Text("Every key goes to the program until it exits; Ctrl-C reaches it, not the console.")
        self._terminal = urwid.Terminal(spec.command, env=spec.env, main_loop=loop)
        urwid.connect_signal(self._terminal, "closed", self._closed)
        self._frame = _PaneFrame(self, urwid.Frame(self._terminal, footer=urwid.AttrMap(self._banner, "footer")))

    def widget(self) -> urwid.Widget:
        return self._frame

    def _closed(self, *_: object) -> None:
        self.exit_code = read_exit_status(self._status)
        self.finished = True
        said = f"exit code {self.exit_code}" if self.exit_code is not None else "no exit code (the program was cut off)"
        self._banner.set_text(f"Finished with {said}. Press Enter to continue.")

    def finish(self) -> None:
        shutil.rmtree(self._dir, ignore_errors=True)
        self._on_exit(self.exit_code)

    def on_hangup(self) -> None:
        """The console's own terminal closed: close the pty, as the terminal closing would."""
        # urwid 2.6 forks the child on first render; before that there is no pid to end,
        # and Terminal.terminate() raises on it.
        if getattr(self._terminal, "pid", None) is not None:
            self._terminal.terminate()
