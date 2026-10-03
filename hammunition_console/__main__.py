# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import sys
from collections.abc import Mapping, Sequence
from typing import TextIO

from hammunition_console import __version__
from hammunition_console.helptext import full_help


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    environ: Mapping[str, str] | None = None,
    euid: int | None = None,
) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    env = os.environ if environ is None else environ
    uid = os.geteuid() if euid is None else euid
    if args in (["--help"], ["-h"]):
        print(full_help(), file=stdout)
        return 0
    if args == ["--version"]:
        print(f"hammunition-console {__version__}", file=stdout)
        return 0
    if args:
        print(f"hammunition-console: unknown argument {args[0]!r} (see --help)", file=sys.stderr)
        return 2
    if uid == 0:
        print(
            "hammunition-console: do not run this as root. It runs as you and asks for sudo "
            "itself, inside a terminal pane, only for the commands that need it.",
            file=sys.stderr,
        )
        return 2
    if not (stdin.isatty() and stdout.isatty()):
        print("hammunition-console needs a terminal (stdin and stdout must both be one).",
              file=sys.stderr)
        return 2
    if env.get("TERM", "dumb") == "dumb":
        print("hammunition-console: TERM is 'dumb' or unset; it cannot draw a screen.",
              file=sys.stderr)
        return 2
    from hammunition_console.app import run  # imported late: the refusals above need no urwid

    return int(run(env))


if __name__ == "__main__":
    sys.exit(main())
