"""Import a script under scripts/, whose hyphenated name can't be imported by name."""

import importlib.util
import pathlib
from types import ModuleType

SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "scripts"


def load_script(filename: str) -> ModuleType:
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
