"""Logging setup."""

import logging
import os


def setup() -> None:
    """Configure the root logger."""
    logging.basicConfig(level=os.getenv("NOTES_LOG_LEVEL", "INFO"))
