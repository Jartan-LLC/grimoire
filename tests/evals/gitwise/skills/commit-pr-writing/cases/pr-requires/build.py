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


git("checkout", "-q", "-b", "feature/note-tags")
write(
    "notes/tags.py",
    '"""Tags on notes."""\n\n\ndef tags(note: str) -> list[str]:\n    """The #words in a note."""\n    return [w[1:] for w in note.split() if w.startswith("#") and len(w) > 1]\n',
)
write(
    "tests/test_tags.py",
    'from notes.tags import tags\n\n\ndef test_tags() -> None:\n    assert tags("buy #milk now") == ["milk"]\n',
)
commit(
    "feat(notes): read #tags from a note",
    "Tags let a later search filter notes without a schema change.",
)
