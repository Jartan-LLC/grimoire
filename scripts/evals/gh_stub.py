"""A stand-in for the GitHub CLI in an eval session: it records each call and answers from the case's replies.

The runner installs this file as `bin/gh` in a sample's sandbox, beside
`gh-stub/replies.json` (the case's `[[gh]]` tables) and `gh-stub/calls.jsonl` (the log it
appends to). It reaches no network and uses only the standard library. A call no reply
matches fails, so a session never reads a success the case did not script.

It does not parse gh's flags, whose arity varies by command (`pr create -f` takes no
value, `api -f` does). It logs the argv as given, then the text of every regular file an
argument or a part of one names (`candidates`) inside its roots, and stdin when one of
those is `-`. The roots are the sandbox and the temp directories the runner names in the
TEMP_ROOTS variable, an `os.pathsep` list; without that variable, the sandbox alone. That
can include a file no gh command would read, and misses only one outside the roots.

A change to what this stub answers, how it matches a call or what it logs, or to the
remote setup in `session.py`, changes what a remote session can do: bump REMOTE_RUNNER
there, so no remote sample drawn before it is reused.
"""

import json
import os
import pathlib
import re
import sys
from collections.abc import Callable, Mapping, Sequence

# A two-character short flag with its value attached, `-bText` or `-Fbody=@b.md`.
SHORT = re.compile(r"-[A-Za-z].+", re.DOTALL)
# A key and its value, `--body=Text` or `body=@b.md`; a space before the `=` makes it text.
KEY = re.compile(r"[^\s=]+=(.*)", re.DOTALL)
STDIN = "-"
MAX_BYTES = 1 << 20
# Commands whose files and stdin are not logged: `gh secret set -f .env` reads a dotenv.
# Any argument equal to one counts, since gh takes flags before the command (`-R o/r secret`).
PRIVATE = ("secret", "variable", "auth")
# The runner's temp directory and `/tmp`: an agent writes a body file to `/tmp/pr-body.md`
# with the Write tool, which the session's TMPDIR (the sandbox's `tmp`) does not redirect.
TEMP_ROOTS = "GRIMOIRE_GH_STUB_TEMP"


def candidates(arg: str) -> list[str]:
    """The argument, and every text gh could read from it as a value, in the order found.

    Each step looks only at the shape of the text, never at a flag's meaning: the rest
    after a two-character short flag (`-bText`), the rest after a key's `=` (`--body=Text`,
    `body=@b.md`), and the text past one leading `@`. They repeat, so `--field=body=@b.md`
    gives `b.md`; a space before the `=` (`x = 1`) keeps a body whole.
    """
    found: list[str] = []
    todo = [arg]
    while todo:
        text = todo.pop(0)
        if text in found:
            continue
        found.append(text)
        if SHORT.fullmatch(text):
            todo.append(text[2:])
        if key := KEY.match(text):
            todo.append(key.group(1))
        if text.startswith("@"):
            todo.append(text[1:])
    return found


def call_line(argv: Sequence[str]) -> str:
    r"""The argv joined with spaces, each newline written as `\n`, so a call is one line."""
    return " ".join(arg.replace("\n", "\\n") for arg in argv)


def answer(replies: Sequence[Mapping[str, object]], argv: list[str]) -> tuple[str, int] | None:
    """The stdout and exit code of the first reply whose `match` finds the call's `call_line`."""
    line = call_line(argv)
    for reply in replies:
        if re.search(str(reply["match"]), line):
            code = reply.get("exit", 0)
            return str(reply.get("stdout", "")), code if isinstance(code, int) else 0
    return None


def _readable(name: str, cwd: pathlib.Path, roots: Sequence[pathlib.Path]) -> pathlib.Path | None:
    """The regular file `name` names from `cwd`, or None: a directory, a FIFO, a device, an invalid name.

    A file under none of `roots` is None too: the session runs as the user, and an argument
    could name their credentials or `/proc/self/environ`.
    """
    try:
        path = (cwd / name).resolve()
        if not any(path.is_relative_to(root.resolve()) for root in roots):
            return None
        return path if path.is_file() else None
    except (OSError, ValueError, RuntimeError):  # a name too long, a NUL byte, a symlink loop
        return None


def record(
    argv: list[str],
    read_stdin: Callable[[], str],
    cwd: pathlib.Path,
    roots: Sequence[pathlib.Path],
) -> dict[str, object]:
    """The call's log entry: its argv, its stdin, and the text of each file its `candidates` name under `roots`.

    Stdin is read only when a candidate is `-`, so a call that names none cannot hang on
    an open stdin. A byte that is not UTF-8 is read as U+FFFD. A file over MAX_BYTES is
    listed under `over_cap`, unread. A `PRIVATE` command's files and stdin are not read.
    """
    names = list(dict.fromkeys(c for arg in argv for c in candidates(arg)))
    private = any(arg in PRIVATE for arg in argv)
    stdin = read_stdin() if STDIN in names and not private else ""
    files: dict[str, str] = {}
    over_cap: list[str] = []
    for name in names:
        path = None if private or name == STDIN else _readable(name, cwd, roots)
        if path is None:
            continue
        try:
            with path.open("rb") as file:
                data = file.read(MAX_BYTES + 1)
        except OSError:
            continue
        if len(data) > MAX_BYTES:
            over_cap.append(name)
        else:
            files[name] = data.decode(errors="replace")
    entry: dict[str, object] = {"argv": argv, "stdin": stdin, "files": files}
    if over_cap:
        entry["over_cap"] = over_cap
    return entry


def main(argv: list[str], state: pathlib.Path) -> int:
    """Log the call to `state/calls.jsonl`, then print the scripted reply or fail."""
    temps = os.environ.get(TEMP_ROOTS, "").split(os.pathsep)
    entry = record(
        argv,
        lambda: sys.stdin.buffer.read().decode(errors="replace"),
        pathlib.Path.cwd(),
        (state.parent, *(pathlib.Path(t) for t in temps if t)),
    )
    # One write to an O_APPEND file, so the log lines of calls made in parallel cannot interleave.
    log = os.open(state / "calls.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    try:
        os.write(log, (json.dumps(entry) + "\n").encode())
    finally:
        os.close(log)
    replies = json.loads((state / "replies.json").read_text())
    reply = answer(replies, argv)
    if reply is None:
        print(f"gh stub: no reply for: {call_line(argv)}", file=sys.stderr)
        return 1
    sys.stdout.write(reply[0])
    return reply[1]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], pathlib.Path(__file__).resolve().parent.parent / "gh-stub"))
