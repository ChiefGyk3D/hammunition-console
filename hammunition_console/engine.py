# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read the engine's JSON documents. The only module that spawns `hammunition --json`.

The version floor is read from the `engine` field of a document, never from
`hammunition --version` (which prints to stderr and emits no document under
--json). ENGINE_FLOOR is a single constant; raise it when the engine release that
ships E1 and E2 is tagged.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from hammunition_console import guard, verbs

ENGINE_FLOOR: tuple[int, int, int] = (0, 19, 0)
SUPPORTED_SCHEMA = "hammunition/1"
INSTALL_PAGE = "https://chiefgyk3d.github.io/Hammunition/getting-started/install/"


class EngineError(Exception):
    """Anything that stops a read."""


class EngineMissing(EngineError):
    pass


class EngineTooOld(EngineError):
    pass


class UnknownSchema(EngineError):
    pass


class BadDocument(EngineError):
    pass


class EngineRefused(EngineError):
    """The engine printed an `error` document: it has no JSON form or refused before planning."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.message = message


@dataclass(frozen=True)
class Document:
    kind: str
    engine: str
    schema: str
    exit_code: int
    body: Mapping[str, Any]


def parse_version(text: str) -> tuple[int, int, int]:
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", text.strip())
    if not m:
        raise BadDocument(f"the engine reported a version the console cannot read: {text!r}")
    return int(m[1]), int(m[2]), int(m[3])


def parse_document(stdout: str, exit_code: int, stderr: str = "") -> Document:
    if not stdout.strip():
        raise BadDocument(f"the engine printed no document (exit {exit_code}): {stderr.strip()[:300]}")
    try:
        body = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise BadDocument(f"the engine printed something that is not JSON (exit {exit_code}): {exc.msg}") from exc
    if not isinstance(body, dict) or not all(isinstance(body.get(k), str) for k in ("schema", "kind", "engine")):
        raise BadDocument("the engine's document lacks schema, kind or engine")
    schema = str(body["schema"])
    if schema != SUPPORTED_SCHEMA:
        raise UnknownSchema(
            f"the engine printed a document of schema {schema!r}; this console knows only "
            f"{SUPPORTED_SCHEMA!r}. Update hammunition-console."
        )
    return Document(str(body["kind"]), str(body["engine"]), schema, exit_code, body)


def accept(doc: Document, floor: tuple[int, int, int] = ENGINE_FLOOR) -> Document:
    have = parse_version(doc.engine)
    if have < floor:
        want = ".".join(str(n) for n in floor)
        raise EngineTooOld(
            f"Hammunition {doc.engine} is older than this console needs ({want} or later). "
            "Update the engine (in its checkout: git pull, then ./bootstrap.sh) and start the console again."
        )
    if doc.kind == "error":
        raise EngineRefused(int(doc.body.get("exit_code", doc.exit_code)), str(doc.body.get("message", "")))
    return doc


Runner = Callable[..., "subprocess.CompletedProcess[str]"]


class Engine:
    def __init__(
        self,
        binary: str = "hammunition",
        environ: Mapping[str, str] | None = None,
        run: Runner = subprocess.run,
    ) -> None:
        self.binary = binary
        self._environ = environ
        self._run = run

    def command(self, *words: str) -> list[str]:
        return [self.binary, *words]

    def read(self, *words: str, timeout: float = 180.0) -> Document:
        verbs.require_json_verb(words)
        guard.assert_clean_read(words)
        argv = [self.binary, *words, "--json"]
        env = guard.scrubbed_environ(os.environ if self._environ is None else self._environ)
        try:
            done = self._run(argv, capture_output=True, text=True, timeout=timeout, env=env,
                             stdin=subprocess.DEVNULL, check=False)
        except FileNotFoundError as exc:
            raise EngineMissing(
                f"{self.binary!r} was not found on PATH. The console runs the engine's own commands and "
                f"cannot work without it. Install the engine first: {INSTALL_PAGE} (run ./bootstrap.sh)."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise EngineError(f"`{' '.join(words)}` timed out after {int(timeout)} s") from exc
        return accept(parse_document(done.stdout, done.returncode, done.stderr))


def command_words(argv: Sequence[str]) -> str:
    """For messages: the verb words of an argv, never its values."""
    return " ".join(w for w in argv if not w.startswith("-"))[:80]
