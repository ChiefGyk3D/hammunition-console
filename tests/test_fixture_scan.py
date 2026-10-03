# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import getpass
import socket

from tests.fixture_scan import PRODUCT_NAMES, findings, host_pattern


def test_placeholders_are_clean() -> None:
    assert findings('{"callsign": "N0CALL", "alt": "N0TST", "grid": "FN31pr", "path": "/home/user/x"}') == []


def test_a_real_looking_callsign_is_found() -> None:
    assert any("callsign" in f for f in findings('{"callsign": "ZZ9ZZ"}'))
    assert any("callsign" in f for f in findings("QQ1QQ"))


def test_a_real_looking_grid_is_found() -> None:
    assert any("grid" in f for f in findings('{"grid_square": "JJ00aa"}'))


def test_a_real_home_path_is_found() -> None:
    assert any("home" in f for f in findings("/home/someoneelse/.config"))


def test_the_live_username_and_hostname_are_found() -> None:
    user = getpass.getuser()
    if len(user) >= 3:
        assert findings(f"owner {user}")
    host = socket.gethostname().split(".")[0]
    if len(host) >= 3:
        assert findings(f"on user@{host}")


def test_an_ordinary_hostname_is_found_as_a_bare_word() -> None:
    pattern = host_pattern("example")
    assert pattern.search("on example today")
    assert not pattern.search("example/1 or /var/example/logs or example-tray")


def test_a_hostname_that_is_a_product_name_counts_only_in_machine_contexts() -> None:
    assert "hammunition" in PRODUCT_NAMES
    pattern = host_pattern("hammunition")
    for text in ("user@hammunition", "hammunition.local", "hostname: hammunition"):
        assert pattern.search(text), text
    for text in ('"schema": "hammunition/1"', "hammunition install station", "/state/hammunition/logs"):
        assert not pattern.search(text), text


def test_a_serial_by_id_path_is_found() -> None:
    assert findings("/dev/serial/by-id/usb-Silicon_Labs_CP2105_0123ABCD-if00")
    assert findings("/dev/serial/by-id/usb-FIXTURE-if00") == []
