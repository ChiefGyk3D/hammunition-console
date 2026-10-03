# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import socket

import pytest


def test_a_test_cannot_reach_the_network() -> None:
    with socket.socket() as sock, pytest.raises(AssertionError, match="the console fetches nothing"):
        sock.settimeout(1)
        sock.connect(("93.184.216.34", 80))  # closed on exit: create_connection leaks the socket it failed to connect


def test_the_package_has_no_network_imports() -> None:
    from pathlib import Path

    forbidden = ("import socket", "import urllib", "import http", "import requests", "import ssl", "from urllib", "from http")
    package = Path(__file__).resolve().parent.parent / "hammunition_console"
    hits = [f"{p.name}: {tok}" for p in package.rglob("*.py") for tok in forbidden if tok in p.read_text()]
    assert hits == [], "the console fetches nothing; the engine does"
