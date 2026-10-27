"""The sandbox's `gh` stub: what it records, and that it answers only what a case scripted."""

import json
import pathlib
import subprocess

import pytest
from evals import gh_stub, session
from evals.proc import run
from evals.suite import Reply


def replies(*pairs: tuple[str, str]) -> list[dict[str, object]]:
    return [{"match": match, "stdout": stdout, "exit": 0} for match, stdout in pairs]


def test_answer_takes_the_first_reply_whose_match_finds_the_joined_argv() -> None:
    scripted = replies(("^pr create", "first"), ("--draft", "second"))
    assert gh_stub.answer(scripted, ["pr", "create", "--draft"]) == ("first", 0)
    assert gh_stub.answer(scripted, ["pr", "edit", "--draft"]) == ("second", 0)
    assert gh_stub.answer(scripted, ["pr", "view", "12"]) is None
    failing = [{"match": "^pr ready", "stdout": "", "exit": 1}]
    assert gh_stub.answer(failing, ["pr", "ready", "12"]) == ("", 1)


def test_answer_matches_a_call_with_a_multi_line_argument_as_one_line() -> None:
    argv = ["pr", "create", "--body", "Fixes it.\n\nCloses #42", "--draft"]
    assert gh_stub.call_line(argv) == "pr create --body Fixes it.\\n\\nCloses #42 --draft"
    assert gh_stub.answer(replies(("^pr create.*--draft$", "made")), argv) == ("made", 0)


@pytest.mark.parametrize(
    ("argv", "refs"),
    [
        (["pr", "create", "--body-file", "b.md"], ["b.md"]),
        (["pr", "create", "--body-file=b.md"], ["b.md"]),
        (["pr", "create", "-F", "b.md"], ["b.md"]),
        (["pr", "create", "-F", "-"], ["-"]),
        (["api", "x", "-F", "body=@b.md", "-F", "event=COMMENT"], ["b.md"]),
        (["api", "x", "--field", "body=@-"], ["-"]),
        (["api", "x", "--input", "q=1.json"], ["q=1.json"]),
        (["api", "x", "--input=-"], ["-"]),
        (["release", "create", "v1", "--notes-file", "n.md"], ["n.md"]),
        (["release", "create", "v1", "-F", "n.md"], ["n.md"]),
        (["pr", "create", "--body", "-F b.md"], []),
        (["pr", "create", "-F"], []),
    ],
)
def test_file_refs_names_each_file_gh_would_read(argv: list[str], refs: list[str]) -> None:
    assert gh_stub.file_refs(argv) == refs


def test_record_reads_body_files_and_stdin_only_when_the_call_names_it(
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "b.md").write_text("Closes #42\n")

    def no_stdin() -> str:
        raise AssertionError("stdin read for a call that does not name it")

    entry, missing = gh_stub.record(["pr", "create", "--body-file", "b.md"], no_stdin, tmp_path)
    assert entry == {
        "argv": ["pr", "create", "--body-file", "b.md"],
        "stdin": "",
        "files": {"b.md": "Closes #42\n"},
    }
    assert missing == []
    entry, missing = gh_stub.record(
        ["api", "x", "-F", "body=@-", "-F", "x=@gone.md"], lambda: "piped", tmp_path
    )
    assert (entry["stdin"], entry["files"], missing) == ("piped", {}, ["gone.md"])


def test_the_stub_logs_a_body_that_is_not_utf8(tmp_path: pathlib.Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    session.install_gh(sandbox, (Reply("^pr create", "made"),))
    (tmp_path / "b.md").write_bytes(b"Body \xff\n")
    for argv, stdin in ((["-F", "b.md"], b""), (["-F", "-"], b"Piped \xfe")):
        made = run(
            [str(sandbox / "bin" / "gh"), "pr", "create", *argv],
            cwd=tmp_path, input=stdin, capture_output=True, check=False,
        )  # fmt: skip
        assert (made.returncode, made.stdout) == (0, b"made")
    calls = session.gh_calls(sandbox)
    assert calls[0]["files"] == {"b.md": "Body \ufffd\n"}
    assert calls[1]["stdin"] == "Piped \ufffd"


def run_stub(
    sandbox: pathlib.Path, cwd: pathlib.Path, *argv: str
) -> subprocess.CompletedProcess[str]:
    return run(
        [str(sandbox / "bin" / "gh"), *argv],
        cwd=cwd,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )


def test_the_installed_stub_logs_every_call_and_fails_one_it_has_no_reply_for(
    tmp_path: pathlib.Path,
) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    session.install_gh(
        sandbox, (Reply("^pr create", "https://github.com/o/r/pull/7\n"), Reply("^pr ready", "", 1))
    )
    work = tmp_path / "repo"
    work.mkdir()
    (work / "b.md").write_text("Closes #42\n")
    created = run_stub(sandbox, work, "pr", "create", "--draft", "--body-file", "b.md")
    assert (created.returncode, created.stdout) == (0, "https://github.com/o/r/pull/7\n")
    assert run_stub(sandbox, work, "pr", "ready", "7").returncode == 1
    unscripted = run_stub(sandbox, work, "pr", "view", "7")
    assert unscripted.returncode == 1
    assert unscripted.stdout == ""
    assert unscripted.stderr == "gh stub: no reply for: pr view 7\n"
    calls = session.gh_calls(sandbox)
    assert [c["argv"] for c in calls] == [
        ["pr", "create", "--draft", "--body-file", "b.md"],
        ["pr", "ready", "7"],
        ["pr", "view", "7"],
    ]
    assert calls[0]["files"] == {"b.md": "Closes #42\n"}
    assert json.loads((sandbox / "gh-stub" / "replies.json").read_text())[1]["exit"] == 1
    assert list((sandbox / "gh-config").iterdir()) == []
