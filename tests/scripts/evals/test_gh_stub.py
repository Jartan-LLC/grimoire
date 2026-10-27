"""The sandbox's `gh` stub: what it records, and that it answers only what a case scripted."""

import json
import os
import pathlib
import subprocess
from typing import cast

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
    ("arg", "found"),
    [
        ("--body=Text", ["--body=Text", "Text"]),
        ("-bText", ["-bText", "Text"]),
        ("-Fbody=@b.md", ["-Fbody=@b.md", "body=@b.md", "@b.md", "b.md"]),
        ("--field=body=@b.md", ["--field=body=@b.md", "body=@b.md", "@b.md", "b.md"]),
        ("@-", ["@-", "-"]),
        ("-Fix typo", ["-Fix typo", "ix typo"]),
        ("x = 1 =Closes", ["x = 1 =Closes"]),
        ("cc @alice", ["cc @alice"]),
        ("-F", ["-F"]),
    ],
)
def test_candidates_are_the_argument_and_its_tails_by_shape_alone(
    arg: str, found: list[str]
) -> None:
    assert gh_stub.candidates(arg) == found


def no_stdin() -> str:
    raise AssertionError("stdin read for a call that names no `-`")


def test_record_reads_each_file_an_argument_names_and_stdin_only_for_a_dash(
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "b.md").write_text("Closes #42\n")
    entry = gh_stub.record(["pr", "create", "--body-file", "b.md"], no_stdin, tmp_path, (tmp_path,))
    assert entry == {
        "argv": ["pr", "create", "--body-file", "b.md"],
        "stdin": "",
        "files": {"b.md": "Closes #42\n"},
    }
    argv = ["api", "x", "-F", "body=@-", "-F", "x=@gone.md"]
    entry = gh_stub.record(argv, lambda: "piped", tmp_path, (tmp_path,))
    assert (entry["stdin"], entry["files"]) == ("piped", {})


def test_record_reads_a_body_file_outside_the_working_directory(tmp_path: pathlib.Path) -> None:
    body = tmp_path / "elsewhere" / "b.md"
    body.parent.mkdir()
    body.write_text("Closes #42\n")
    work = tmp_path / "repo"
    work.mkdir()
    entry = gh_stub.record(["pr", "create", "-F", str(body)], no_stdin, work, (tmp_path,))
    assert entry["files"] == {str(body): "Closes #42\n"}


def test_record_reads_nothing_that_is_not_a_regular_file(tmp_path: pathlib.Path) -> None:
    (tmp_path / "dir").mkdir()
    os.mkfifo(tmp_path / "fifo")
    names = ["dir", "missing.md", "fifo", "/dev/zero", "x" * 300, "nul\0byte"]
    argv = ["pr", "create", *(arg for name in names for arg in ("--body-file", name))]
    entry = gh_stub.record(argv, no_stdin, tmp_path, (tmp_path,))
    assert (entry["files"], "over_cap" in entry) == ({}, False)
    inline = gh_stub.record(["pr", "create", "--body", "y" * 300], no_stdin, tmp_path, (tmp_path,))
    assert inline["files"] == {}


def test_record_notes_a_file_over_the_cap_unread(tmp_path: pathlib.Path) -> None:
    (tmp_path / "big.md").write_bytes(b"x" * (gh_stub.MAX_BYTES + 1))
    (tmp_path / "cap.md").write_bytes(b"x" * gh_stub.MAX_BYTES)
    argv = ["pr", "create", "-F", "big.md", "--body-file=cap.md"]
    entry = gh_stub.record(argv, no_stdin, tmp_path, (tmp_path,))
    assert entry["over_cap"] == ["big.md"]
    assert list(cast("dict[str, str]", entry["files"])) == ["cap.md"]


@pytest.mark.parametrize(
    "argv",
    [
        ["secret", "set", "-f", ".env"],
        ["-R", "o/r", "secret", "set", "--env-file=.env"],
        ["variable", "set", "-f", ".env"],
        ["auth", "login", "--with-token", "-"],
    ],
)
def test_record_reads_no_file_or_stdin_of_a_secret_variable_or_auth_call(
    tmp_path: pathlib.Path, argv: list[str]
) -> None:
    (tmp_path / ".env").write_text("TOKEN=hunter2\n")
    entry = gh_stub.record(argv, no_stdin, tmp_path, (tmp_path,))
    assert (entry["argv"], entry["stdin"], entry["files"]) == (argv, "", {})


def sandbox_and_temp(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[pathlib.Path, tuple[pathlib.Path, pathlib.Path]]:
    """The sandbox's repo, and the roots: the sandbox and a temp root, beside a fake HOME."""
    work = tmp_path / "sandbox" / "repo"
    work.mkdir(parents=True)
    (tmp_path / "tmp").mkdir()
    (tmp_path / "home").mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    return work, (work.parent, tmp_path / "tmp")


def test_record_reads_a_file_under_the_sandbox_or_the_temp_root(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    work, roots = sandbox_and_temp(tmp_path, monkeypatch)
    (work / "b.md").write_text("Closes #42\n")
    body = tmp_path / "tmp" / "pr-body.md"
    body.write_text("Fixes #7\n")
    entry = gh_stub.record(["pr", "create", "-F", "b.md", "-F", str(body)], no_stdin, work, roots)
    assert entry["files"] == {"b.md": "Closes #42\n", str(body): "Fixes #7\n"}


@pytest.mark.parametrize("name", ["/proc/self/environ", "../../home/creds", "link.md"])
def test_record_reads_no_file_under_neither_root(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    work, roots = sandbox_and_temp(tmp_path, monkeypatch)
    (tmp_path / "home" / "creds").write_text("secret\n")
    (work / "link.md").symlink_to(tmp_path / "home" / "creds")
    entry = gh_stub.record(["pr", "create", "-F", name], no_stdin, work, roots)
    assert entry["files"] == {}


def test_the_stub_logs_a_body_that_is_not_utf8(tmp_path: pathlib.Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    session.install_gh(sandbox, (Reply("^pr create", "made"),))
    (sandbox / "b.md").write_bytes(b"Body \xff\n")
    for argv, stdin in ((["-F", "b.md"], b""), (["-F", "-"], b"Piped \xfe")):
        made = run(
            [str(sandbox / "bin" / "gh"), "pr", "create", *argv],
            cwd=sandbox, input=stdin, capture_output=True, check=False,
        )  # fmt: skip
        assert (made.returncode, made.stdout) == (0, b"made")
    calls = session.gh_calls(sandbox)
    assert calls[0]["files"] == {"b.md": "Body \ufffd\n"}
    assert calls[1]["stdin"] == "Piped \ufffd"


def run_stub(
    sandbox: pathlib.Path, cwd: pathlib.Path, *argv: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return run(
        [str(sandbox / "bin" / "gh"), *argv],
        cwd=cwd,
        env=env,
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
    work = sandbox / "repo"
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


def test_the_installed_stub_answers_a_call_whose_arguments_name_no_file(
    tmp_path: pathlib.Path,
) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    session.install_gh(sandbox, (Reply("^pr create", "made"),))
    made = run_stub(sandbox, tmp_path, "pr", "create", "--title", "-Fix typo", "-F", "gone.md")
    assert (made.returncode, made.stdout, made.stderr) == (0, "made", "")
    assert session.gh_calls(sandbox)[0]["files"] == {}


def test_the_installed_stub_reads_a_file_under_each_temp_root_only_when_the_runner_names_it(
    tmp_path: pathlib.Path,
) -> None:
    sandbox = tmp_path / "sandbox"
    (sandbox / "repo").mkdir(parents=True)
    session.install_gh(sandbox, (Reply("^pr create", "made"),))
    bodies = [tmp_path / temp / "pr-body.md" for temp in ("runner-tmp", "tmp")]
    for body in bodies:
        body.parent.mkdir()
        body.write_text(f"Closes #{len(body.parent.name)}\n")
    unset = {k: v for k, v in os.environ.items() if k != gh_stub.TEMP_ROOTS}
    named = unset | {gh_stub.TEMP_ROOTS: os.pathsep.join(str(b.parent) for b in bodies)}
    for env in (named, unset):
        argv = ("pr", "create", "-F", str(bodies[0]), "--body-file", str(bodies[1]))
        assert run_stub(sandbox, sandbox / "repo", *argv, env=env).returncode == 0
    assert [c["files"] for c in session.gh_calls(sandbox)] == [
        {str(bodies[0]): "Closes #10\n", str(bodies[1]): "Closes #3\n"},
        {},
    ]
