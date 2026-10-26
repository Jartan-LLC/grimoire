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
