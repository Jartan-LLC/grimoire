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
    "slug",
    [
        (
            "feat(util): add trim helper",
            "Trims whitespace from both ends of user input before it is stored.",
        ),
        (
            "fix(util): fix typo in the docstring from the previous commit",
            'The previous commit added a docstring with a typo ("whitspace"). This commit fixes it.\n\nI noticed it while reviewing the diff, so I fixed it here instead of amending.',
        ),
        (
            "feat(util): add pad helper",
            "Pads short values to a fixed width for the report columns.",
        ),
        (
            "fix(util): correct wording I introduced in the last commit",
            'In the last commit I wrote "colums" in the docstring; this corrects it to "columns".',
        ),
    ],
)
git("checkout", "-q", "-b", "feature/slugify")
write(
    "slug/__init__.py",
    '"""URL slugs."""\n\nimport re\n\n\ndef slugify(text: str) -> str:\n    """Retrun `text` lower-cased with runs of non-alphanumerics turned into one hyphen."""\n    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")\n',
)
write(
    "tests/test_slug.py",
    'from slug import slugify\n\n\ndef test_slugify() -> None:\n    assert slugify("Hello, World!") == "hello-world"\n',
)
commit(
    "feat(slug): add slugify for URL slugs",
    "Titles become URL path segments, so they need a stable ASCII form.",
)
push_to_origin("feature/slugify")
