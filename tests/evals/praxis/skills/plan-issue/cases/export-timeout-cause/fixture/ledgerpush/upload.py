"""Send the export file to the accountant."""

import socket

from ledgerpush import config


def upload(path):
    with socket.create_connection((config.HOST, 22), timeout=config.TIMEOUT) as conn:
        conn.sendall(open(path, "rb").read())
