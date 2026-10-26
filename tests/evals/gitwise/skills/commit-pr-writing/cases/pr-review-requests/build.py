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


git("checkout", "-q", "-b", "feature/slugify")
write(
    "slug/__init__.py",
    '"""URL slugs."""\n\nimport re\n\n\ndef slugify(text: str) -> str:\n    """Return `text` lower-cased with runs of non-alphanumerics turned into one hyphen."""\n    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")\n',
)
write(
    "tests/test_slug.py",
    'from slug import slugify\n\n\ndef test_slugify() -> None:\n    assert slugify("Hello, World!") == "hello-world"\n',
)
commit(
    "feat(slug): add slugify for URL slugs",
    "Titles become URL path segments, so they need a stable ASCII form.",
)
write(
    "tests/test_slug.py",
    'from slug import slugify\n\n\ndef test_slugify() -> None:\n    assert slugify("Hello, World!") == "hello-world"\n\n\ndef test_only_punctuation() -> None:\n    assert slugify("!!!") == ""\n',
)
commit("test(slug): cover text that is all punctuation")
