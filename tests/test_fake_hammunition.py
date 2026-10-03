# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import subprocess
import sys
from pathlib import Path

from tests import fake_hammunition as fake
from tests.helpers import load, make_shim

FAKE = Path(fake.__file__)


def test_status_comes_from_its_fixture() -> None:
    out, code = fake.respond(["hammunition", "status", "--json"]) or ("", -1)
    assert code == 0 and json.loads(out) == load("status")


def test_exit_codes_come_from_the_sidecar() -> None:
    out, code = fake.respond(["hammunition", "update", "--json"], suffix="-without") or ("", -1)
    assert code == 2 and json.loads(out)["kind"] == "error"


def test_install_dry_run_returns_a_plan_and_refused_names_return_the_refusal() -> None:
    out, code = fake.respond(["hammunition", "install", "station", "--dry-run", "--json"]) or ("", -1)
    assert json.loads(out)["kind"] == "plan" and code == 0
    out, code = fake.respond(["hammunition", "install", "no-such-unit-xyz", "--dry-run", "--json"]) or ("", -1)
    assert json.loads(out)["outcome"] == "refused" and code == 2


def test_station_show_follows_the_station_variant() -> None:
    out, _ = fake.respond(["hammunition", "station", "show", "--json"], station="none") or ("", -1)
    assert json.loads(out)["callsign"] is None


def test_an_unmapped_argv_is_none() -> None:
    assert fake.respond(["hammunition", "hardware", "list", "--json"]) is None


def run_shim(tmp: Path, *args: str, stdin: int | None = subprocess.DEVNULL) -> subprocess.CompletedProcess[str]:
    shim = make_shim(tmp)
    env = {**os.environ, "PATH": f"{shim}:{os.environ['PATH']}"}
    return subprocess.run(["hammunition", *args], capture_output=True, text=True, env=env, stdin=stdin)


def test_a_real_install_without_a_tty_is_refused_like_the_engine(tmp_path: Path) -> None:
    done = run_shim(tmp_path, "install", "station")
    assert done.returncode == 3 and "no interactive terminal" in done.stderr


def test_an_unmapped_read_fails_loudly(tmp_path: Path) -> None:
    done = run_shim(tmp_path, "hardware", "list", "--json")
    assert done.returncode == 99 and "FAKE: unmapped" in done.stderr


def test_the_invocation_log_records_argv_tty_and_consent_looking_variables(tmp_path: Path) -> None:
    log = tmp_path / "log.jsonl"
    shim = make_shim(tmp_path)
    env = {**os.environ, "PATH": f"{shim}:{os.environ['PATH']}", "FAKE_HAMMUNITION_LOG": str(log),
           "HAMMUNITION_ACCEPT_RF_RESEARCH": "1"}
    subprocess.run(["hammunition", "status", "--json"], env=env, capture_output=True, stdin=subprocess.DEVNULL)
    entry = json.loads(log.read_text().splitlines()[0])
    assert entry["argv"] == ["status", "--json"] and entry["tty"] is False
    assert "HAMMUNITION_ACCEPT_RF_RESEARCH" in entry["env"]


def test_the_script_runs_standalone_with_the_current_interpreter() -> None:
    done = subprocess.run([sys.executable, str(FAKE), "--version"], capture_output=True, text=True)
    assert done.returncode == 0 and done.stdout.startswith("hammunition ")
