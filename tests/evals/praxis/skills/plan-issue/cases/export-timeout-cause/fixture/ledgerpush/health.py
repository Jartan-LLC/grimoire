"""A quick reachability check for the monitoring page."""

import socket

from ledgerpush import config


def reachable():
    try:
        socket.create_connection((config.HOST, 22), timeout=config.TIMEOUT).close()
    except OSError:
        return False
    return True
