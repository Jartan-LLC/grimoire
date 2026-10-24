"""Put scripts/ on the import path, so the tests import the `evals` package as eval.py does."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
