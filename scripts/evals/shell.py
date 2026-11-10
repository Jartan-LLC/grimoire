"""Which files a Bash command writes through the shell, read from its text without running it.

Counted: a redirect to a file (`>`, `>>`, `>|`, `&>`, `&>>`, with or without a file
descriptor number, a heredoc's command included), `tee`, and `sed -i` or `perl -i`. Not
counted: a redirect to `/dev/...` or to another descriptor (`2>&1`, `>&2`), text inside
quotes or a heredoc body, and a file a program the command runs writes itself (`cp`,
`mv`, `git`, `python3 - <<EOF` with `open(p, 'w')`), whose path the shell does not show.

`write_failed` reads a command's output for a write that failed; the trace also fails
every write of a call that never ran.

The reading is a tokenizer, not a shell parser. A heredoc body runs from the line after
its `<<WORD` to the first line that is just WORD; quotes nest one level, so a double
quote inside `"$(...)"` ends the string early; a path with an unquoted `$(...)` in it
ends at the `$`; a backtick substitution is read as plain words, so `` `echo > t` ``
records `` t` ``; `pushd` is not read as `cd`; a prefix word's own options are not
skipped, so `sudo -u x tee f` is not read as `tee`; and a command run as a string
(`bash -c "..."`) is not read.
"""

import posixpath
import re
from collections.abc import Iterator
from typing import NamedTuple

# A heredoc operator and its delimiter word, quoted or not; `<<<` is a here-string.
_HEREDOC = re.compile(r"""(?<!<)<<(?!<)(-?)\s*\\?(['"]?)([^\s'"<>;&|()]+)\2""")
_TOKEN = re.compile(
    r"""
    (?P<space>[ \t\r]+|\\\n)
    | (?P<comment>\#[^\n]*)
    | (?P<op>\(\(|\)\)|&>>?|\d*>>|\d*>[|&]?|\d*<<<|\d*<<-?|\d*<[&>]?|\|\||&&|;;|[|&;()\n])
    | (?P<word>(?:[^\s'"\\;&|()<>]|\\.|'[^']*'|"(?:[^"\\]|\\.)*")+)
    | (?P<other>.)
    """,
    re.VERBOSE | re.DOTALL,
)
_QUOTED = re.compile(r"""'([^']*)'|"((?:[^"\\]|\\.)*)"|\\(.)""", re.DOTALL)
_ESCAPED = re.compile(r"\\(.)", re.DOTALL)
_ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=")
# Tokens that open and close `(( ))` and `[[ ]]`, where a `>` compares and redirects nothing.
_COMPARING = {"((": 1, "[[": 1, "))": -1, "]]": -1}
# Words that run the command after them.
_PREFIXES = frozenset(
    ("if", "elif", "while", "until", "then", "do", "else", "!", "{", "time", "env", "command",
     "exec", "nohup", "sudo")
)  # fmt: skip


class _Editor(NamedTuple):
    """The options of an in-place editor that take a value.

    Attributes:
        script: Short option letters that take the script, as the rest of the word or the
            next word.
        value: Short option letters that take some other value the same way.
        attached: Short option letters that take the rest of the word only.
        long_script: Long options that take the script, after `=` or as the next word.
        long_value: Long options that take some other value the same way.
    """

    script: str
    value: str
    attached: str
    long_script: tuple[str, ...] = ()
    long_value: tuple[str, ...] = ()


_EDITORS = {
    "sed": _Editor("ef", "l", "", ("--expression", "--file"), ("--line-length",)),
    "perl": _Editor("eE", "", "MmIxdDC"),
}
# How bash, tee, sed and perl report a file they could not write: a prefix, the path, a reason.
_PREFIX_FAILED = r"(?:bash: (?:line \d+: )?|tee: |sed: can't read |sed: couldn't edit |Can't open )"
_REASON_FAILED = (
    r"'?: (?:No such file or directory|Permission denied|Is a directory|Not a directory"
    r"|Read-only file system|cannot overwrite existing file|not a regular file)"
)


def _unquoted(word: str) -> str:
    """`word` as the shell passes it: quotes removed, escapes resolved."""

    def one(match: re.Match[str]) -> str:
        if match[1] is not None:
            return match[1]
        if match[2] is not None:
            return _ESCAPED.sub(r"\1", match[2])
        return match[3]

    return _QUOTED.sub(one, word)


def _without_heredocs(command: str) -> str:
    """`command` with every heredoc body dropped; a heredoc with no closing line is left whole."""
    lines = command.split("\n")
    kept: list[str] = []
    at = 0
    while at < len(lines):
        line = lines[at]
        kept.append(line)
        at += 1
        for dash, _, word in _HEREDOC.findall(line):
            closing = (
                i
                for i in range(at, len(lines))
                if (lines[i].lstrip("\t") if dash else lines[i]) == word
            )
            end = next(closing, None)
            if end is not None:
                at = end + 1
    return "\n".join(kept)


def _tokens(command: str) -> Iterator[tuple[str, str]]:
    """The (kind, text) tokens of `command`: `op` or `word`, words unquoted."""
    text = _without_heredocs(command)
    for match in _TOKEN.finditer(text):
        kind = str(match.lastgroup)
        if kind == "op":
            yield kind, match[0]
        elif kind == "word":
            yield kind, _unquoted(match[0])


def _writes_to(op: str, target: str) -> bool:
    """Whether redirect `op` with word `target` opens a file for writing."""
    if ">" not in op or "<" in op:  # `<` reads, and so does `<>`
        return False
    if op.endswith("&") and not op.startswith("&"):
        return not re.fullmatch(r"\d+|-", target)  # `>&2` and `>&-` name descriptors
    return True


class _Simple(NamedTuple):
    """A simple command of a command line.

    Attributes:
        words: Its words, unquoted.
        targets: The files its redirects write.
        end: The operator after it. A `(` or `)` ends a command with no words too, so that
            the caller sees every subshell open and close.
    """

    words: list[str]
    targets: list[str]
    end: str


def _simple_commands(command: str) -> Iterator[_Simple]:
    """Each simple command of `command`, in order."""
    words: list[str] = []
    targets: list[str] = []
    redirect: str | None = None
    comparing = 0
    for kind, text in [*_tokens(command), ("op", "\n")]:
        comparing = max(0, comparing + _COMPARING.get(text, 0))
        if redirect is not None:
            if kind == "word" and not comparing and _writes_to(redirect, text):
                targets.append(text)
            redirect = None
            if kind == "word":
                continue
        if kind == "word":
            words.append(text)
        elif ">" in text or "<" in text:
            redirect = text
        elif words or targets or text in ("(", ")"):
            yield _Simple(words, targets, text)
            words, targets = [], []


def _edited_files(tool: str, args: list[str]) -> list[str]:
    """The files `sed` or `perl` with arguments `args` edits in place; none unless `-i` is given."""
    editor = _EDITORS[tool]
    in_place, script_given = False, False
    operands: list[str] = []
    at = 0
    while at < len(args):
        arg = args[at]
        at += 1
        if arg == "--":
            operands += args[at:]
            break
        if arg.startswith("--"):
            name = arg.split("=", 1)[0]
            in_place = in_place or name == "--in-place"
            script_given = script_given or name in editor.long_script
            if name in editor.long_script + editor.long_value and "=" not in arg:
                at += 1  # skip the value word
            continue
        if not arg.startswith("-") or arg == "-":
            operands.append(arg)
            continue
        for offset, letter in enumerate(arg[1:], start=2):
            if letter == "i":
                in_place = True
                break
            if letter in editor.attached:
                break
            if letter in editor.script or letter in editor.value:
                script_given = script_given or letter in editor.script
                if offset == len(arg):
                    at += 1  # skip the value word
                break
    if not in_place:
        return []
    return operands if script_given else operands[1:]


def _command(words: list[str]) -> list[str]:
    """Simple command `words` without the prefix words and assignments before its command."""
    while words and (words[0] in _PREFIXES or _ASSIGNMENT.match(words[0])):
        words = words[1:]
    return words


def _command_files(words: list[str]) -> list[str]:
    """The files `words`, a command past its prefixes, writes as arguments: `tee`'s or an editor's."""
    if not words:
        return []
    tool, args = posixpath.basename(words[0]), words[1:]
    if tool == "tee":
        return [a for a in args if not a.startswith("-")]
    if tool in _EDITORS:
        return _edited_files(tool, args)
    return []


def file_writes(command: str) -> list[str]:
    """The paths shell `command` writes, each once, in order.

    A relative path is joined to the directory a `cd` earlier in the same command moved
    to, unless that `cd` ran in a subshell, `( ... )` or `$( ... )`, that has since ended.
    The directory the command starts in is not known, so a path relative to it stays
    relative, and so does one that starts with a variable or `~`, as written. A `cd` to a
    `~` path is kept as written too, so `cd ~ && cat > b` records `~/b`.
    """
    found: list[str] = []
    cwd = ""
    outer: list[str] = []  # the directory outside each subshell the command is in
    for simple in _simple_commands(command):
        words = _command(simple.words)
        if words[:1] == ["cd"]:
            to = next((w for w in words[1:] if not w.startswith("-")), "")
            cwd = "" if not to else to if to[:1] == "~" else posixpath.join(cwd, to)
        else:
            for path in [*_command_files(words), *simple.targets]:
                if not path.startswith("/dev/"):
                    joined = posixpath.join(cwd, path) if cwd and path[:1] not in "$~" else path
                    if joined not in found:
                        found.append(joined)
        if simple.end == "(":
            outer.append(cwd)
        elif simple.end == ")" and outer:
            cwd = outer.pop()
    return found


def write_failed(path: str, output: str) -> bool:
    """Whether a command's `output` shows that its write to `path` failed.

    A Bash call's exit status is its last command's, so a write followed by a failing
    test still wrote its file, and a failed redirect followed by `ls` still failed. The
    message names the path as the command wrote it, before any `cd` join: it is matched
    by its last part.
    """
    name = re.escape(posixpath.basename(path))
    return re.search(rf"{_PREFIX_FAILED}(?:[^\s:]*/)?{name}{_REASON_FAILED}", output) is not None
