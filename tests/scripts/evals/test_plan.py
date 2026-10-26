import pathlib

from evals.plan import covered_by, expand, target
from evals.suite import load_suite
from helpers import write_suite


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
