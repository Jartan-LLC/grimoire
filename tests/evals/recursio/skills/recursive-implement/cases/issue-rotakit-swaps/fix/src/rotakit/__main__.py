"""Run the rotakit command: python -m rotakit."""

import sys

from rotakit.cli import main

__all__: list[str] = []

sys.exit(main())
