# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MARK = "# Installed by hammunition-console install.sh."


def sh(script: str, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(ROOT / script), *args], capture_output=True, text=True, env=env or os.environ.copy())


def install(prefix: Path) -> subprocess.CompletedProcess[str]:
    return sh("install.sh", "--prefix", str(prefix), "--interpreter", sys.executable)


def test_install_places_the_tree_the_wrapper_and_the_man_page(tmp_path: Path) -> None:
    done = install(tmp_path)
    assert done.returncode == 0, done.stderr
    wrapper = tmp_path / "bin" / "hammunition-console"
    assert os.access(wrapper, os.X_OK) and MARK in wrapper.read_text().splitlines()
    tree = tmp_path / "share" / "hammunition-console" / "hammunition_console"
    assert (tree / "__main__.py").exists() and not list(tree.rglob("__pycache__"))
    assert (tmp_path / "share" / "man" / "man1" / "hammunition-console.1").exists()
    ran = subprocess.run([str(wrapper), "--version"], capture_output=True, text=True)
    assert ran.returncode == 0 and ran.stdout.startswith("hammunition-console ")


def test_the_wrapper_bakes_in_the_interpreter_and_never_uses_a_shell_string(tmp_path: Path) -> None:
    install(tmp_path)
    text = (tmp_path / "bin" / "hammunition-console").read_text()
    assert f'exec "{sys.executable}" -P -m hammunition_console "$@"' in text


def test_reinstalling_is_idempotent_and_replaces_the_tree(tmp_path: Path) -> None:
    install(tmp_path)
    stale = tmp_path / "share" / "hammunition-console" / "hammunition_console" / "stale.py"
    stale.write_text("x")
    assert install(tmp_path).returncode == 0 and not stale.exists()


def test_a_wrapper_this_installer_did_not_write_is_left_alone(tmp_path: Path) -> None:
    (tmp_path / "bin").mkdir()
    foreign = tmp_path / "bin" / "hammunition-console"
    foreign.write_text("#!/bin/sh\necho mine\n")
    done = install(tmp_path)
    assert done.returncode == 1 and "not replaced" in done.stderr and foreign.read_text().endswith("echo mine\n")


@pytest.mark.parametrize("args,needle", [
    (["--prefix", "relative/dir"], "absolute"),
    (["--interpreter", "python3"], "absolute"),
    (["--prefix"], "needs"),
    (["--bogus"], "unknown option"),
])
def test_bad_arguments_are_refused_with_exit_2(args: list[str], needle: str, tmp_path: Path) -> None:
    done = sh("install.sh", *args)
    assert done.returncode == 2 and needle in done.stderr


def test_an_interpreter_that_is_not_python_311_with_urwid_is_refused_before_anything_is_written(tmp_path: Path) -> None:
    notpython = tmp_path / "notpython"
    notpython.write_text("#!/bin/sh\nexit 1\n")
    notpython.chmod(0o755)
    prefix = tmp_path / "prefix"
    prefix.mkdir()
    done = sh("install.sh", "--prefix", str(prefix), "--interpreter", str(notpython))
    assert done.returncode == 1 and "3.11" in done.stderr
    assert list(prefix.iterdir()) == []


def test_help_prints_usage_and_exits_0() -> None:
    for script in ("install.sh", "uninstall.sh"):
        done = sh(script, "--help")
        assert done.returncode == 0 and "--prefix" in done.stdout


def test_uninstall_removes_what_install_placed_and_leaves_the_config(tmp_path: Path) -> None:
    install(tmp_path)
    config = tmp_path / ".config" / "hammunition-console"
    config.mkdir(parents=True)
    (config / "config.toml").write_text("theme = 'dark'\n")
    done = sh("uninstall.sh", "--prefix", str(tmp_path))
    assert done.returncode == 0, done.stderr
    assert not (tmp_path / "bin" / "hammunition-console").exists()
    assert not (tmp_path / "share" / "hammunition-console").exists()
    assert not (tmp_path / "share" / "man" / "man1" / "hammunition-console.1").exists()
    assert (config / "config.toml").exists() and "config.toml" in done.stdout
    assert sh("uninstall.sh", "--prefix", str(tmp_path)).returncode == 0, "uninstall is idempotent"


def test_uninstall_leaves_a_foreign_wrapper(tmp_path: Path) -> None:
    (tmp_path / "bin").mkdir()
    foreign = tmp_path / "bin" / "hammunition-console"
    foreign.write_text("#!/bin/sh\necho mine\n")
    done = sh("uninstall.sh", "--prefix", str(tmp_path))
    assert done.returncode == 0 and foreign.exists() and "not written by" in done.stdout


def test_the_in_tree_wrapper_runs_the_package_beside_it(tmp_path: Path) -> None:
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    (fakebin / "python3").symlink_to(sys.executable)
    env = {**os.environ, "PATH": f"{fakebin}:{os.environ['PATH']}"}
    ran = subprocess.run([str(ROOT / "bin" / "hammunition-console"), "--version"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert ran.returncode == 0 and ran.stdout.startswith("hammunition-console ")


def test_the_in_tree_wrapper_follows_a_symlink(tmp_path: Path) -> None:
    link = tmp_path / "hc"
    link.symlink_to(ROOT / "bin" / "hammunition-console")
    fakebin = tmp_path / "pybin"
    fakebin.mkdir()
    (fakebin / "python3").symlink_to(sys.executable)
    ran = subprocess.run([str(link), "--version"], capture_output=True, text=True,
                         env={**os.environ, "PATH": f"{fakebin}:{os.environ['PATH']}"})
    assert ran.returncode == 0


def test_shellcheck_is_clean() -> None:
    if shutil.which("shellcheck") is None:
        if os.environ.get("HAMMUNITION_REQUIRE_SHELLCHECK") == "1":
            pytest.fail("shellcheck is required here and is not installed")
        pytest.skip("shellcheck not installed (CI requires it)")
    done = subprocess.run(["shellcheck", "install.sh", "uninstall.sh", "bin/hammunition-console"], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout
