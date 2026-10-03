# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run one command with this process's terminal, and record how it ended.

    runner.py STATUS_FILE -- COMMAND...

Started by the pane inside urwid.Terminal. It exists for two reasons: the
console must learn the child's exit status without relying on how any urwid
version reports a child's death, and Ctrl-C must reach the child, not kill the
thing watching it. A *handler* (not SIG_IGN) is installed for SIGINT: handlers
are reset to the default across exec, so the child still gets the default
action, while this process just waits.
"""

from __future__ import annotations

import signal
import subprocess
import sys


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] != "--":
        print("usage: runner.py STATUS_FILE -- COMMAND...", file=sys.stderr)
        return 2
    status_path, command = argv[0], argv[2:]
    signal.signal(signal.SIGINT, lambda *_: None)
    try:
        code = subprocess.Popen(command).wait()
    except FileNotFoundError:
        print(f"{command[0]}: command not found", file=sys.stderr)
        code = 127
    except OSError as exc:
        print(f"{command[0]}: cannot run ({exc.strerror})", file=sys.stderr)
        code = 126
    if code < 0:
        code = 128 + (-code)
    try:
        with open(status_path, "w", encoding="utf-8") as handle:
            handle.write(f"{code}\n")
    except OSError:
        pass
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
