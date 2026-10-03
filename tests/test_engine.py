# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import subprocess
from typing import Any

import pytest

from hammunition_console import engine
from hammunition_console.engine import (
    ENGINE_FLOOR,
    BadDocument,
    Engine,
    EngineMissing,
    EngineRefused,
    EngineTooOld,
    UnknownSchema,
)
from hammunition_console.verbs import NotAJsonVerb
from tests.helpers import load


def doc(**over: Any) -> str:
    base = {"schema": "hammunition/1", "kind": "status", "engine": "0.19.0"}
    return json.dumps({**base, **over})


@pytest.mark.parametrize("text,expected", [("0.19.0", (0, 19, 0)), ("1.2.3+dev", (1, 2, 3)), ("v0.20.1", (0, 20, 1))])
def test_parse_version(text: str, expected: tuple[int, int, int]) -> None:
    assert engine.parse_version(text) == expected


def test_unparsable_version_is_a_bad_document() -> None:
    with pytest.raises(BadDocument):
        engine.parse_version("banana")


def test_the_floor_is_the_measured_spike_version() -> None:
    assert ENGINE_FLOOR == (0, 20, 0)


def test_parse_a_recorded_document() -> None:
    d = engine.parse_document(json.dumps(load("status")), 0)
    assert (d.kind, d.schema, d.exit_code) == ("status", "hammunition/1", 0) and d.body["target"]


@pytest.mark.parametrize("stdout", ["", "not json", "[1]", '{"kind": "x"}'])
def test_garbage_is_a_bad_document(stdout: str) -> None:
    with pytest.raises(BadDocument):
        engine.parse_document(stdout, 0, "boom")


@pytest.mark.parametrize("schema", ["hammunition/2", "other/1", "hammunition/1.5", "hammunition"])
def test_an_unknown_schema_is_refused_by_name(schema: str) -> None:
    with pytest.raises(UnknownSchema, match=schema.replace(".", r"\.")):
        engine.parse_document(doc(schema=schema), 0)


def test_the_floor_names_both_versions_and_the_update_command() -> None:
    with pytest.raises(EngineTooOld) as info:
        engine.accept(engine.parse_document(doc(engine="0.18.9"), 0))
    text = str(info.value)
    assert "0.18.9" in text and "0.19.0" in text and "git pull" in text and "bootstrap.sh" in text


def test_an_error_document_raises_with_the_engines_words() -> None:
    d = engine.parse_document(json.dumps(load("update-all-without")), 2)
    with pytest.raises(EngineRefused) as info:
        engine.accept(d)
    assert info.value.exit_code == 2 and "retired" in info.value.message


def test_a_refused_plan_is_a_plan_not_an_error() -> None:
    d = engine.accept(engine.parse_document(json.dumps(load("plan-refused")), 2))
    assert d.kind == "plan" and d.body["outcome"] == "refused" and d.exit_code == 2


class Recorder:
    def __init__(self, stdout: str = "", code: int = 0, error: BaseException | None = None) -> None:
        self.calls: list[tuple[list[str], dict[str, Any]]] = []
        self.stdout, self.code, self.error = stdout, code, error

    def __call__(self, argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append((argv, kw))
        if self.error:
            raise self.error
        return subprocess.CompletedProcess(argv, self.code, self.stdout, "")


def test_read_builds_a_fixed_argv_and_scrubs_the_environment() -> None:
    rec = Recorder(json.dumps(load("status")))
    eng = Engine(environ={"PATH": "/bin", "HAMMUNITION_ACCEPT_RF_RESEARCH": "1", "X_CONSENT": "1"}, run=rec)
    eng.read("status")
    argv, kw = rec.calls[0]
    assert argv == ["hammunition", "status", "--json"]
    assert kw["env"] == {"PATH": "/bin"} and kw["stdin"] == subprocess.DEVNULL
    assert kw.get("shell") in (None, False)


def test_names_stay_single_argv_elements() -> None:
    rec = Recorder(json.dumps(load("plan-station")))
    Engine(run=rec).read("install", "a b", "--dry-run")
    assert rec.calls[0][0] == ["hammunition", "install", "a b", "--dry-run", "--json"]


def test_a_missing_engine_names_the_command_and_the_install_page() -> None:
    with pytest.raises(EngineMissing, match="hammunition"):
        Engine(run=Recorder(error=FileNotFoundError())).read("status")


def test_a_timeout_is_an_engine_error_not_a_hang() -> None:
    with pytest.raises(engine.EngineError, match="timed out"):
        Engine(run=Recorder(error=subprocess.TimeoutExpired("hammunition", 1))).read("status", timeout=1)


def test_a_verb_with_no_json_form_never_spawns() -> None:
    rec = Recorder()
    with pytest.raises(NotAJsonVerb):
        Engine(run=rec).read("hardware", "list")
    assert rec.calls == []


def test_the_floor_is_checked_on_every_document() -> None:
    eng = Engine(run=Recorder(doc(engine="0.1.0")))
    with pytest.raises(EngineTooOld):
        eng.read("status")


def test_command_prefixes_the_binary() -> None:
    assert Engine(binary="hammunition").command("install", "station") == ["hammunition", "install", "station"]


def test_the_default_timeout_is_180_and_none_is_passed_through() -> None:
    rec = Recorder(json.dumps(load("status")))
    eng = Engine(environ={"PATH": "/bin"}, run=rec)
    eng.read("status")
    assert rec.calls[0][1]["timeout"] == 180.0
    rec2 = Recorder(json.dumps(load("plan-station")))
    Engine(environ={"PATH": "/bin"}, run=rec2).read("install", "station", "--dry-run", timeout=None)
    assert rec2.calls[0][1]["timeout"] is None
