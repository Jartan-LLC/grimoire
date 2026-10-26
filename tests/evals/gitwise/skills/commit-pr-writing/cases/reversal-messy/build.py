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
    "prices",
    [
        (
            "feat(rates): cache exchange rates in a dict",
            "Rates are kept in memory for the process lifetime.",
        ),
        ("feat(rates): store exchange rates in sqlite", "Use sqlite now."),
        (
            "feat(taxes): load tax tables from a CSV file",
            "Tables are read from data/taxes.csv on startup.",
        ),
        ("feat(taxes): load tax tables from the API", "Switched to the API."),
    ],
)
git("checkout", "-q", "-b", "feature/price-cache")
write(
    "prices/__init__.py",
    '"""Look up product prices."""\n\n_CACHE: dict[str, float] = {}\n\n\ndef price(sku: str, fetch) -> float:\n    """The price of `sku`, fetched once and then cached in memory."""\n    if sku not in _CACHE:\n        _CACHE[sku] = fetch(sku)\n    return _CACHE[sku]\n',
)
write(
    "tests/test_prices.py",
    'from prices import price\n\n\ndef test_fetches_once() -> None:\n    calls = []\n    def fetch(sku):\n        calls.append(sku)\n        return 1.5\n    assert price("a", fetch) == price("a", fetch) == 1.5\n    assert calls == ["a"]\n',
)
commit(
    "feat(prices): keep the price cache in memory",
    "Prices are cached in a module-level dict for the life of the process, so a\nrepeated lookup costs no request.",
)
push_to_origin("feature/price-cache")
