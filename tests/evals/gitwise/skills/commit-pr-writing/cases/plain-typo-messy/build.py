"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def commit(subject: str, body: str = "") -> None:
    git("add", "-A")
    git("commit", "-q", "-m", subject, *(["-m", body] if body else []))


def push_to_origin(*branches: str) -> None:
    git("init", "-q", "--bare", "../origin.git")
    git("remote", "add", "origin", "../origin.git")
    git("push", "-q", "-u", "origin", *branches)


def habit(package: str, commits: list[tuple[str, str]]) -> None:
    """Earlier commits on the current branch, each adding a small helper, with these messages."""
    for n, (subject, body) in enumerate(commits, 1):
        write(
            f"{package}/helper_{n}.py",
            f'"""Helper {n}."""\n\n\ndef helper_{n}() -> int:\n    """Return {n}."""\n    return {n}\n',
        )
        commit(subject, body)


habit(
    "calc",
    [
        (
            "docs: fix typo in docstring",
            "## Summary\n\nFixes a typo.\n\n## Changes\n\n- Fixed the typo in the docstring.\n\n## Testing\n\n- Ran the tests; they pass.\n\n## Notes\n\nNo behaviour change.",
        ),
        (
            "docs: fix grammar in README",
            "## Summary\n\nFixes grammar.\n\n## Changes\n\n- README grammar.\n\n## Testing\n\n- Not needed, docs only.\n\n## Notes\n\nNone.",
        ),
        (
            "docs: fix spelling of 'integer'",
            "## Summary\n\nSpelling.\n\n## Changes\n\n- One word.\n\n## Testing\n\n- N/A\n\n## Notes\n\nNone.",
        ),
    ],
)
