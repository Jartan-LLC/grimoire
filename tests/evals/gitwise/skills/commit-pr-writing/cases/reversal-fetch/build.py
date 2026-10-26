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


git("checkout", "-q", "-b", "feature/fetch")
write(
    "crawl/__init__.py",
    '"""Fetch pages."""\n\nfrom collections.abc import Callable\n\n\ndef fetch_all(urls: list[str], fetch: Callable[[str], str]) -> list[str]:\n    """Every page in `urls`, one after another."""\n    return [fetch(url) for url in urls]\n',
)
write(
    "tests/test_crawl.py",
    'from crawl import fetch_all\n\n\ndef test_order() -> None:\n    assert fetch_all(["a", "b"], str.upper) == ["A", "B"]\n',
)
commit(
    "feat(crawl): fetch pages one at a time",
    "Sequential fetching keeps the load on each site to one request.",
)
push_to_origin("feature/fetch")
