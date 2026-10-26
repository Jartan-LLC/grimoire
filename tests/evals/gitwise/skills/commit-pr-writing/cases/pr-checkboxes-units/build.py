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
    "units",
    [
        (
            "feat(units): add grams to ounces (#3)",
            "## What\n\nAdds grams_to_ounces.\n\n## Checklist\n\n- [x] Tests added\n- [x] Tests pass\n- [ ] Changelog",
        ),
        (
            "fix(units): round to two places (#5)",
            "## What\n\nRounds results.\n\n## Checklist\n\n- [x] Tests pass\n- [x] Docs updated",
        ),
    ],
)
git("checkout", "-q", "-b", "feature/celsius")
write(
    "units/temperature.py",
    '"""Temperature."""\n\n\ndef c_to_f(c: float) -> float:\n    """Celsius as Fahrenheit."""\n    return c * 9 / 5 + 32\n',
)
write(
    "tests/test_temperature.py",
    "from units.temperature import c_to_f\n\n\ndef test_boiling() -> None:\n    assert c_to_f(100) == 212\n",
)
commit(
    "feat(units): convert Celsius to Fahrenheit",
    "Weather data arrives in Celsius; the app shows Fahrenheit.",
)
