"""A stand-in for the GitHub CLI in an eval session: it records each call and answers from the case's replies.

The runner installs this file as `bin/gh` in a sample's sandbox, beside
`gh-stub/replies.json` (the case's `[[gh]]` tables) and `gh-stub/calls.jsonl` (the log it
appends to). It reaches no network and uses only the standard library. A call no reply
matches fails, so a session never reads a success the case did not script.

A change to what this stub answers, how it matches a call or what it logs, or to the
remote setup in `session.py`, changes what a remote session can do: bump REMOTE_RUNNER
there, so no remote sample drawn before it is reused.
"""

import json
import os
import pathlib
import re
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence

# gh reads a file for these: `pr create --body-file`, `release create --notes-file`,
# `api --input`, each naming a path.
PATH_FLAGS = ("--body-file", "--notes-file", "--input")
# `-F` is the short `--body-file` or `--notes-file`, and `api`'s `--field`, a file only as
# `key=@path`.
FIELD_FLAGS = ("-F", "--field")
STDIN = "-"


def flag_values(argv: Sequence[str], flags: Sequence[str]) -> Iterator[tuple[str, str]]:
    """Each (flag, value) in `argv` for one of `flags`, given as `--flag value` or `--flag=value`."""
    for i, arg in enumerate(argv):
        flag, eq, inline = arg.partition("=")
        if flag in flags:
            yield flag, inline if eq else (argv[i + 1] if i + 1 < len(argv) else "")


def file_refs(argv: list[str]) -> list[str]:
    """The files a call tells gh to read, in order; `-` stands for stdin."""
    found: list[str] = []
    for flag, value in flag_values(argv, (*PATH_FLAGS, *FIELD_FLAGS)):
        if flag in FIELD_FLAGS and "=" in value:
            key_value = value.partition("=")[2]
            if key_value.startswith("@"):
                found.append(key_value[1:])
        elif value:
            found.append(value)
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


def record(
    argv: list[str], read_stdin: Callable[[], str], cwd: pathlib.Path
) -> tuple[dict[str, object], list[str]]:
    """The call's log entry (argv, stdin, each body file's text) and the files it could not read.

    Stdin is read only when the call names it, as gh does, so a call that does not
    cannot hang on an open stdin. A byte that is not UTF-8 is read as U+FFFD, so the call
    is still logged.
    """
    refs = file_refs(argv)
    stdin = read_stdin() if STDIN in refs else ""
    files: dict[str, str] = {}
    missing: list[str] = []
    for ref in refs:
        if ref == STDIN:
            continue
        try:
            files[ref] = (cwd / ref).read_text(errors="replace")
        except OSError:
            missing.append(ref)
    return {"argv": argv, "stdin": stdin, "files": files}, missing


def main(argv: list[str], state: pathlib.Path) -> int:
    """Log the call to `state/calls.jsonl`, then print the scripted reply or fail."""
    entry, missing = record(
        argv, lambda: sys.stdin.buffer.read().decode(errors="replace"), pathlib.Path.cwd()
    )
    # One write to an O_APPEND file, so the log lines of calls made in parallel cannot interleave.
    log = os.open(state / "calls.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    try:
        os.write(log, (json.dumps(entry) + "\n").encode())
    finally:
        os.close(log)
    if missing:
        print(f"gh stub: cannot read {', '.join(missing)}", file=sys.stderr)
        return 1
    replies = json.loads((state / "replies.json").read_text())
    reply = answer(replies, argv)
    if reply is None:
        print(f"gh stub: no reply for: {call_line(argv)}", file=sys.stderr)
        return 1
    sys.stdout.write(reply[0])
    return reply[1]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], pathlib.Path(__file__).resolve().parent.parent / "gh-stub"))
