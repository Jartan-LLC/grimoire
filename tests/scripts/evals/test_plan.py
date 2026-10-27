import pathlib

from evals.plan import covered_by, expand, first_gate, listed, target
from evals.suite import Suite, load_suite
from helpers import SUITE, write_suite


def test_target_names_the_skill_agent_or_command_a_file_belongs_to() -> None:
    assert target("plugins/gitwise/skills/commit-pr-writing/SKILL.md") == (
        "gitwise",
        "commit-pr-writing",
    )
    assert target("plugins/gitwise/skills/github-conventions/issue-format.md") == (
        "gitwise",
        "github-conventions",
    )
    assert target("plugins/praxis/agents/doc-reviewer.md") == ("praxis", "doc-reviewer")
    assert target("plugins/praxis/hooks/hooks.json") is None
    assert target("scripts/eval.py") is None


def test_expand_follows_pointers_until_nothing_new_is_reached() -> None:
    references = {
        "plugins/praxis/agents/general-reviewer.md": {("gitwise", "github-conventions")},
        "plugins/praxis/skills/review-pr/SKILL.md": {("praxis", "general-reviewer")},
        "plugins/praxis/skills/plain-writing/SKILL.md": {("praxis", "docs-patterns")},
    }
    assert expand(["plugins/gitwise/skills/github-conventions/SKILL.md"], references) == [
        "plugins/gitwise/skills/github-conventions/SKILL.md",
        "plugins/praxis/agents/general-reviewer.md",
        "plugins/praxis/skills/review-pr/SKILL.md",
    ]


def test_covered_by_matches_the_suites_globs(tmp_path: pathlib.Path) -> None:
    suite = load_suite(write_suite(tmp_path))
    files = [
        "plugins/gitwise/skills/commit-pr-writing/SKILL.md",
        "plugins/gitwise/skills/commit-pr-writing/references/x.md",
        "plugins/gitwise/skills/github-conventions/SKILL.md",
    ]
    assert covered_by(suite, files) == files[:2]


def _suite(root: pathlib.Path, *covers: str, models: str = "") -> Suite:
    globs = ", ".join(f'"{c}"' for c in covers)
    config = SUITE.replace(
        'covers = ["plugins/gitwise/skills/commit-pr-writing/**"]', f"covers = [{globs}]\n{models}"
    )
    return load_suite(write_suite(root, config))


def test_listed_marks_a_suite_direct_only_when_it_covers_a_changed_file(
    tmp_path: pathlib.Path,
) -> None:
    hub = "plugins/gitwise/skills/github-conventions/SKILL.md"
    reviewer = "plugins/praxis/agents/general-reviewer.md"
    references = {reviewer: {("gitwise", "github-conventions")}}
    hub_suite = _suite(tmp_path / "hub", "plugins/gitwise/skills/github-conventions/**")
    loader_suite = _suite(tmp_path / "loader", reviewer)
    both_suite = _suite(tmp_path / "both", "plugins/gitwise/skills/github-conventions/**", reviewer)
    other_suite = _suite(tmp_path / "other", "plugins/praxis/skills/review-pr/**")
    suites = [hub_suite, loader_suite, both_suite, other_suite]
    got = {e.suite.path.name: (e.hits, e.direct) for e in listed(suites, [hub], references)}
    assert got == {
        "hub": ([hub], True),
        "loader": ([reviewer], False),
        "both": ([hub, reviewer], True),
    }


def test_first_gate_skips_watch_models(tmp_path: pathlib.Path) -> None:
    models = 'models = ["claude-haiku-5-5", "claude-opus-5-5"]\nwatch = ["claude-haiku-5-5"]\n'
    assert first_gate(_suite(tmp_path / "a", "x", models=models)) == "claude-opus-5-5"
    all_watch = 'models = ["claude-haiku-5-5"]\nwatch = ["claude-haiku-5-5"]\n'
    assert first_gate(_suite(tmp_path / "b", "x", models=all_watch)) == "claude-haiku-5-5"
