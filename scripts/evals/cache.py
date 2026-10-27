"""Completed samples, kept in the clone's git directory so every worktree shares them.

The store is `grimoire-evals/` in the git common directory, or `$GRIMOIRE_EVALS_STORE`.
The recorded baselines and verdicts rest on its samples, so it is data, not a cache: it
lives as long as the clone, out of reach of a container restart that clears `~/.cache`,
and git neither tracks nor cleans it. Under `plans/` are each branch's fixed plans:
deleting those drops the pin, so the next screen fixes whatever plan it runs. Rerunning
after a usage-limit stop skips every valid sample already here; excluded ones are retried.
"""

import gzip
import hashlib
import json
import os
import pathlib
from dataclasses import asdict, dataclass
from typing import Any

from .proc import GIT, run

STORE = "GRIMOIRE_EVALS_STORE"


def common_dir(checkout: pathlib.Path) -> pathlib.Path:
    """The git directory every worktree of `checkout`'s clone shares, absolute."""
    common = run(
        [GIT, "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=checkout, capture_output=True, text=True, check=True,
    ).stdout.strip()  # fmt: skip
    return pathlib.Path(common)


def root(checkout: pathlib.Path) -> pathlib.Path:
    """The store: `$GRIMOIRE_EVALS_STORE`, else `grimoire-evals/` in `checkout`'s git common directory.

    The override is made absolute, `~` expanded, as plugin paths in it must be.
    """
    if override := os.environ.get(STORE):
        return pathlib.Path(override).expanduser().resolve()
    return common_dir(checkout) / "grimoire-evals"


def key(case_hash: str, arm_hash: str, model: str, version: str, index: int) -> str:
    """A sample's identity: what its session depended on, and which repeat it is.

    `arm_hash` carries the arm's name, plugin hash and screen, so a sample is reused
    only to resume the screen it was drawn for.
    """
    text = json.dumps([case_hash, arm_hash, model, version, index])
    return hashlib.sha256(text.encode()).hexdigest()[:32]


@dataclass
class Sample:
    """One finished session and what was collected from it."""

    key: str
    case: str
    arm: str
    index: int
    plugins: dict[str, str]
    valid: bool
    reasons: list[str]
    commits: list[str]
    final: str
    files: dict[str, str]
    usage: dict[str, object]
    spoiled: str = ""
    # The `file:` paths the key named at draw time; None in samples drawn before it was kept.
    collected: list[str] | None = None
    # The (agent, skill) pairs the debug log named as preloaded; None before they were kept.
    preloads: list[list[str]] | None = None
    # Each call the sandbox's `gh` recorded (argv, stdin, the files it named); None for a case
    # without a remote, and in samples drawn before it was kept.
    gh: list[dict[str, object]] | None = None


def _paths(store: pathlib.Path, sample_key: str) -> tuple[pathlib.Path, pathlib.Path]:
    folder = store / "samples" / sample_key[:2]
    return folder / f"{sample_key}.json", folder / f"{sample_key}.jsonl.gz"


def load(store: pathlib.Path, sample_key: str) -> Sample | None:
    """The stored sample, or None."""
    path, _ = _paths(store, sample_key)
    if not path.is_file():
        return None
    fields: dict[str, Any] = json.loads(path.read_text())
    return Sample(**fields)


def events_path(store: pathlib.Path, sample_key: str) -> pathlib.Path:
    """Where the sample's raw trace is kept."""
    return _paths(store, sample_key)[1]


def save(store: pathlib.Path, sample: Sample, trace_text: str) -> None:
    """Store the sample and its raw trace; the JSON goes last, so a crash leaves no half sample."""
    path, events = _paths(store, sample.key)
    path.parent.mkdir(parents=True, exist_ok=True)
    events.write_bytes(gzip.compress(trace_text.encode()))
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(asdict(sample), indent=1))
    temporary.replace(path)


def read_events(store: pathlib.Path, sample_key: str) -> str:
    """The raw trace text of a stored sample."""
    return gzip.decompress(events_path(store, sample_key).read_bytes()).decode()
