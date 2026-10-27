import pathlib

import pytest
from evals import lint as lint_module
from evals.lint import lint
from helpers import KEY, SUITE, write_suite

TRACKED = ["plugins/gitwise/skills/commit-pr-writing/SKILL.md"]
VERIFY = """
[[plant]]
id = "off-by-one"
verify = "python3 check.py"
"""


@pytest.fixture
def root(tmp_path: pathlib.Path) -> pathlib.Path:
    skill = tmp_path / "plugins" / "gitwise" / "skills" / "commit-pr-writing"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: commit-pr-writing\n---\n")
    return tmp_path


def suite_at(root: pathlib.Path, suite: str = SUITE, key: str = KEY) -> pathlib.Path:
    case_root = write_suite(
        root / "tests" / "evals" / "gitwise" / "skills" / "commit-pr-writing", suite, key
    )
    case = case_root / "cases" / "c1"
    (case / "reference").mkdir()
    (case / "reference" / "pass-1.toml").write_text(
        'commits = ["fix: y\\n\\nCloses #42"]\nfinal = "Done."\n'
    )
    (case / "reference" / "fail-1.toml").write_text('commits = ["fix: y"]\nfinal = "Done."\n')
    return case


def test_a_well_formed_suite_passes(root: pathlib.Path) -> None:
    suite_at(root)
    assert lint(root, TRACKED) == []


def test_lint_names_a_hint_in_the_prompt_and_a_fact_the_writer_cannot_find(
    root: pathlib.Path,
) -> None:
    case = suite_at(root, key=KEY.replace('text = "42"', 'text = "43"'))
    (case / "prompt.md").write_text("Fix it and keep the issue number.\n")
    found = lint(root, TRACKED)
    assert any("gives away 'issue number'" in f for f in found)
    assert any("fact '43' is not in prompt" in f for f in found)


def test_lint_requires_references_that_pass_and_fail(root: pathlib.Path) -> None:
    case = suite_at(root)
    (case / "reference" / "pass-1.toml").write_text('commits = ["fix: y"]\nfinal = "Done."\n')
    (case / "reference" / "fail-1.toml").write_text(
        'commits = ["fix: y\\n\\n#42"]\nfinal = "Done."\n'
    )
    found = lint(root, TRACKED)
    assert any("reference pass-1 fails kept" in f for f in found)
    assert any("reference fail-1 passes every check" in f for f in found)


def test_lint_grades_a_report_check_on_a_references_reports(root: pathlib.Path) -> None:
    key = KEY.replace('artifact = "commits"', 'artifact = "report:praxis:general-reviewer"')
    case = suite_at(root, key=key)
    (case / "reference" / "pass-1.toml").write_text(
        'final = "Done."\n[reports]\n"praxis:general-reviewer" = "Closes #42"\n'
    )
    assert lint(root, TRACKED) == []
    (case / "reference" / "pass-1.toml").write_text('commits = ["Closes #42"]\nfinal = "Done."\n')
    assert any("reference pass-1 fails kept" in f for f in lint(root, TRACKED))


def test_lint_grades_gh_and_brief_checks_and_wants_a_remote_for_gh(root: pathlib.Path) -> None:
    key = KEY.replace('artifact = "commits"', 'artifact = "gh"')
    key = key.replace('artifact = "final"', 'artifact = "brief:praxis:general-reviewer"')
    case = suite_at(root, key=key)
    (case / "reference" / "pass-1.toml").write_text(
        'gh = "gh pr create --draft\\n\\nCloses #42"\n'
        '[briefs]\n"praxis:general-reviewer" = "Review the fix."\n'
    )
    assert any("a gh check needs remote = true" in f for f in lint(root, TRACKED))
    remote = f"remote = true\n{key}remote_runner = {lint_module.REMOTE_RUNNER}\n"
    (case / "key.toml").write_text(remote)
    assert lint(root, TRACKED) == []
    (case / "reference" / "pass-1.toml").write_text('gh = "gh pr create --draft"\n')
    found = lint(root, TRACKED)
    assert any("reference pass-1 fails kept" in f for f in found)


def test_lint_requires_a_recorded_baseline_failure_on_a_target_case(root: pathlib.Path) -> None:
    suite_at(root, key=KEY.replace("failures = 2", "failures = 0"))
    assert any("needs a [[baseline]] that failed at least once" in f for f in lint(root, TRACKED))


def test_lint_names_a_baseline_drawn_under_an_older_runner(root: pathlib.Path) -> None:
    suite_at(root, key=KEY.replace("runner = 2", "runner = 1"))
    assert any("drawn under runner 1, not 2; redraw it" in f for f in lint(root, TRACKED))


def test_lint_names_a_remote_baseline_drawn_under_another_remote_runner(
    root: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lint_module, "REMOTE_RUNNER", 2)
    case = suite_at(root, key="remote = true\n" + KEY)
    found = lint(root, TRACKED)
    assert any("drawn under remote_runner 0, not 2; redraw it" in f for f in found)
    (case / "key.toml").write_text("remote = true\n" + KEY + "remote_runner = 3\n")
    found = lint(root, TRACKED)
    assert any("drawn under remote_runner 3, not 2; redraw it" in f for f in found)
    (case / "key.toml").write_text("remote = true\n" + KEY + "remote_runner = 2\n")
    assert lint(root, TRACKED) == []
    (case / "key.toml").write_text(KEY)
    assert lint(root, TRACKED) == []


def test_lint_names_a_baseline_drawn_while_a_case_without_a_remote_had_one(
    root: pathlib.Path,
) -> None:
    case = suite_at(root, key=KEY + "remote_runner = 3\n")
    assert lint(root, TRACKED) == [
        f"{case}: the claude-opus-5-5 old baseline was drawn under remote_runner 3, "
        "while the case had a remote; redraw it"
    ]
    (case / "key.toml").write_text(KEY + "remote_runner = 0\n")
    assert lint(root, TRACKED) == []


def test_lint_runs_a_plant_both_ways(root: pathlib.Path) -> None:
    case = suite_at(root, key=KEY + VERIFY)
    (case / "fixture" / "check.py").write_text("import sys\nsys.exit(0)\n")
    found = lint(root, TRACKED)
    assert any("has no fix/" in f for f in found)
    (case / "fix").mkdir()
    (case / "fix" / "check.py").write_text("import sys\nsys.exit(1)\n")
    found = lint(root, TRACKED)
    assert any("verify passes on the fixture" in f for f in found)
    assert any("verify fails with fix/ applied (exit 1)" in f for f in found)


def test_a_real_plant_passes(root: pathlib.Path) -> None:
    case = suite_at(root, key=KEY + VERIFY)
    (case / "fixture" / "check.py").write_text("import sys\nsys.exit(1)\n")
    (case / "fix").mkdir()
    (case / "fix" / "check.py").write_text("import sys\nsys.exit(0)\n")
    assert lint(root, TRACKED) == []


def test_lint_names_suite_level_problems(root: pathlib.Path) -> None:
    suite = SUITE.replace('target = "gitwise:commit-pr-writing"', 'target = "gitwise:missing"')
    suite = 'BURNED = ["c1", "c9"]\n' + suite.replace("commit-pr-writing/**", "nowhere/**")
    suite_at(root, suite=suite, key=KEY.replace('split = "dev"', 'split = "screen"'))
    found = lint(root, TRACKED)
    assert any(
        "covers 'plugins/gitwise/skills/nowhere/**' matches no tracked file" in f for f in found
    )
    assert any("target 'gitwise:missing' is no skill" in f for f in found)
    assert any("BURNED names 'c9'" in f for f in found)
    assert any("burned case 'c1' is still in screen" in f for f in found)


def test_lint_reports_a_suite_that_does_not_load(root: pathlib.Path) -> None:
    suite_at(root, suite=SUITE.replace("[pass_rule]", "[rule]"))
    assert any("no [pass_rule]" in f for f in lint(root, TRACKED))
