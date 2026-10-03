# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import socket
from collections.abc import Iterator
from typing import Any

import pytest
import urwid

urwid.set_encoding("utf-8")


@pytest.fixture(autouse=True)
def _block_remote_sockets(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """No test may talk to anything but a unix socket or loopback."""
    real_connect = socket.socket.connect

    def guarded(self: socket.socket, address: Any) -> Any:
        if self.family == socket.AF_UNIX:
            return real_connect(self, address)
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise AssertionError(f"test tried to connect to {address!r}; the console fetches nothing")
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded)
    yield
