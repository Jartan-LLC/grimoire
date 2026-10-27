"""A stand-in for the GitHub CLI in an eval session: it records each call and answers from the case's replies.

The runner installs this file as `bin/gh` in a sample's sandbox, beside `gh/replies.json`
(the case's `[[gh]]` tables) and `gh/calls.jsonl` (the log it appends to). It reaches no
network and uses only the standard library. A call no reply matches fails, so a session
never reads a success the case did not script.
"""

import json
import pathlib
import re
import sys
from collections.abc import Callable, Mapping, Sequence

# gh reads a file for these: `pr create --body-file`, its short `-F`, and `api -F key=@path`.
FILE_FLAGS = ("--body-file", "-F", "--field")
STDIN = "-"


def file_refs(argv: list[str]) -> list[str]:
    """The files a call tells gh to read, in order; `-` stands for stdin.

    A `--field key=value` names a file only as `key=@path`; any other value is text.
    """
    found: list[str] = []
    for i, arg in enumerate(argv):
        flag, eq, inline = arg.partition("=")
        if flag not in FILE_FLAGS:
            continue
        value = inline if eq else (argv[i + 1] if i + 1 < len(argv) else "")
        if "=" in value:
            key_value = value.partition("=")[2]
            if key_value.startswith("@"):
                found.append(key_value[1:])
        elif value:
            found.append(value)
    return found


def answer(replies: Sequence[Mapping[str, object]], argv: list[str]) -> tuple[str, int] | None:
    """The stdout and exit code of the first reply whose `match` finds the argv joined with spaces."""
    joined = " ".join(argv)
    for reply in replies:
        if re.search(str(reply["match"]), joined):
            code = reply.get("exit", 0)
            return str(reply.get("stdout", "")), code if isinstance(code, int) else 0
    return None


def record(
    argv: list[str], read_stdin: Callable[[], str], cwd: pathlib.Path
) -> tuple[dict[str, object], list[str]]:
    """The call's log entry (argv, stdin, each body file's text) and the files it could not read.

    Stdin is read only when the call names it, as gh does, so a call that does not
    cannot hang on an open stdin.
    """
    refs = file_refs(argv)
    stdin = read_stdin() if STDIN in refs else ""
    files: dict[str, str] = {}
    missing: list[str] = []
    for ref in refs:
        if ref == STDIN:
            continue
        try:
            files[ref] = (cwd / ref).read_text()
        except OSError:
            missing.append(ref)
    return {"argv": argv, "stdin": stdin, "files": files}, missing


def main(argv: list[str], state: pathlib.Path) -> int:
    """Log the call to `state/calls.jsonl`, then print the scripted reply or fail."""
    entry, missing = record(argv, sys.stdin.read, pathlib.Path.cwd())
    with (state / "calls.jsonl").open("a") as log:
        log.write(json.dumps(entry) + "\n")
    if missing:
        print(f"gh stub: cannot read {', '.join(missing)}", file=sys.stderr)
        return 1
    replies = json.loads((state / "replies.json").read_text())
    reply = answer(replies, argv)
    if reply is None:
        print(f"gh stub: no reply for: {' '.join(argv)}", file=sys.stderr)
        return 1
    sys.stdout.write(reply[0])
    return reply[1]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], pathlib.Path(__file__).resolve().parent.parent / "gh"))
