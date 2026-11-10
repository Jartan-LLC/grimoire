import pytest
from evals import shell


@pytest.mark.parametrize(
    ("command", "paths"),
    [
        ("echo x > notes.md", ["notes.md"]),
        ("printf '\\n- x\\n' >> docs/index.md && cat docs/index.md", ["docs/index.md"]),
        ("cat > docs/a.md <<'EOF'\ndef f() -> str:\n    return a > b\nEOF", ["docs/a.md"]),
        ("cat <<EOF > out.md\nx -> y\nEOF\necho done >> log.md", ["out.md", "log.md"]),
        ("cat <<-EOF >> t.md\n\tx > y\n\tEOF", ["t.md"]),
        ("make 2> err.log &> all.log; make >& both.log >| forced.log", ["err.log", "all.log", "both.log", "forced.log"]),
        ('cat a > "my file.md"', ["my file.md"]),
        ("echo x | tee -a log.txt copy.txt | wc -l", ["log.txt", "copy.txt"]),
        ("sed -i 's/a>b/c/' src/x.py && grep -n c src/x.py", ["src/x.py"]),
        ("sed -i.bak -e 's/a/b/' -e 's/c/d/' f1 f2", ["f1", "f2"]),
        ("sed -ie 's/a/b/' f", ["f"]),  # GNU sed reads `-ie` as -i with the suffix e
        ("perl -CSD -pi -e 's/a/b/g' a.ts b.ts", ["a.ts", "b.ts"]),
        ("perl -0pi -e 's/a\\nb/c/' f; perl -lpi -e 's/a/b/' g", ["f", "g"]),
        ("cd /repo/.claude/workspace/x && cat > 3.md <<'EOF'\n# x\nEOF", ["/repo/.claude/workspace/x/3.md"]),
        ('cd /repo; t=$(mktemp -d); echo hi > "$t/a.txt"', ["$t/a.txt"]),
        ("echo $((a > 1)) > n.txt", ["n.txt"]),
        ("[[ $a > $b ]] && echo y > f; [[ a > b && c > d ]] || echo z > g", ["f", "g"]),
        ("cd ~ && cat > b <<'EOF'\nx\nEOF\ncd ~/w; echo x > c", ["~/b", "~/w/c"]),
        ("x=$(git show HEAD:a.py > a.py)", ["a.py"]),
        ("echo a > f; echo b > f", ["f"]),
        ("(cd sub && echo x > a); echo y > b; x=$(cd up; pwd) && echo z > c", ["sub/a", "b", "c"]),
        ("cd a && (cd b; echo x > f) && echo y > g", ["a/b/f", "a/g"]),
        ("{ cd ws; echo a > s.md; }; if true; then cd up; fi; echo b > t.md", ["ws/s.md", "ws/up/t.md"]),
    ],
)  # fmt: skip
def test_file_writes_finds_each_file_the_shell_writes(command: str, paths: list[str]) -> None:
    assert shell.file_writes(command) == paths


@pytest.mark.parametrize(
    "command",
    [
        "make test 2>/dev/null >&2; ls 2>&1 | tail; exec 3>&-",
        "echo x > /dev/null | tee /dev/stderr",
        "echo \"a > b\" 'c > d'",
        'git commit -m "$(cat <<\'EOF\'\nfix: "x" -> y\nEOF\n)"',
        "git commit -F /tmp/msg.txt",
        "sed -n 's/x/y/p' f; perl -ne 'print' f",
        "python3 - <<'EOF'\nopen('a.py', 'w').write(s)\nEOF",
        "cp a.md b.md; mv c.md d.md; touch e.md",
        "echo hi # a comment > x\n",
        "diff <(sort a) <(sort b)",
    ],
)
def test_file_writes_finds_none_where_the_shell_writes_no_file(command: str) -> None:
    assert shell.file_writes(command) == []


@pytest.mark.parametrize(
    ("output", "failed"),
    [
        ("/bin/bash: line 1: docs/a.md: No such file or directory", True),
        ("bash: a.md: cannot overwrite existing file", True),
        ("tee: docs/a.md: Permission denied", True),
        ("sed: can't read a.md: No such file or directory", True),
        ("Exit code 2\nmake: *** No rule to make target 'check'.  Stop.", False),
        ("ls: cannot access 'a.md': No such file or directory", False),
        ("cat: a.md: No such file or directory", False),
        ("bash: line 1: data.md: command not found", False),
    ],
)
def test_write_failed_reads_only_the_writers_own_error(output: str, failed: bool) -> None:
    # The path as recorded after a `cd` join; the message names it as the command wrote it.
    assert shell.write_failed("/repo/docs/a.md", output) is failed
