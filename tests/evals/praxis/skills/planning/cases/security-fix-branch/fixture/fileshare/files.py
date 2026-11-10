"""Serve uploaded files."""

import os

UPLOADS = "uploads"


def serve_file(name):
    with open(os.path.join(UPLOADS, name), "rb") as f:
        return f.read()
