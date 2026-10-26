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


git("checkout", "-q", "-b", "feature/order-ids")
write(
    "orders/__init__.py",
    '"""Order ids."""\n\nimport itertools\n\n_COUNTER = itertools.count(1)\n\n\ndef next_order_id() -> str:\n    """The next order number."""\n    return str(next(_COUNTER))\n',
)
write(
    "tests/test_orders.py",
    "from orders import next_order_id\n\n\ndef test_unique() -> None:\n    assert next_order_id() != next_order_id()\n",
)
commit(
    "feat(orders): number orders sequentially",
    "Sequential numbers are easy to read out over the phone.",
)
push_to_origin("feature/order-ids")
