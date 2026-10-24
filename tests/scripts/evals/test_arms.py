import os
import pathlib

import pytest
from evals import session
from evals.arms import merge_base, new_arm, none_arm, old_arm
from evals.proc import GIT, run


def git(repo: pathlib.Path, *args: str) -> None:
    run(
        [GIT, *args],
        cwd=repo,
        env=session.git_env(dict(os.environ)),
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "repo"
    (root / "plugins" / "demo" / ".claude-plugin").mkdir(parents=True)
    (root / "plugins" / "demo" / ".claude-plugin" / "plugin.json").write_text('{"name": "demo"}\n')
    (root / "plugins" / "demo" / "skills" / "s").mkdir(parents=True)
    (root / "plugins" / "demo" / "skills" / "s" / "SKILL.md").write_text("old\n")
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "start")
    return root


def test_old_arm_is_the_committed_tree_and_new_arm_the_working_tree(
    repo: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    store = tmp_path / "store"
    (repo / "plugins" / "demo" / "skills" / "s" / "SKILL.md").write_text("new\n")
    (repo / "plugins" / "demo" / "skills" / "s" / "extra.md").write_text("untracked\n")
    old, new = old_arm(repo, "main", store), new_arm(repo, store)
    assert pathlib.Path(old.plugins["demo"], "skills/s/SKILL.md").read_text() == "old\n"
    assert pathlib.Path(new.plugins["demo"], "skills/s/SKILL.md").read_text() == "new\n"
    assert pathlib.Path(new.plugins["demo"], "skills/s/extra.md").is_file()
    assert old.hash != new.hash
    assert old_arm(repo, "main", store) == old
    assert new_arm(repo, store) == new


def test_merge_base_leaves_out_what_main_gained_after_the_branch(repo: pathlib.Path) -> None:
    start = subprocess_out(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "-b", "feature")
    git(repo, "checkout", "-q", "main")
    (repo / "plugins" / "demo" / "skills" / "s" / "SKILL.md").write_text("main moved\n")
    git(repo, "commit", "-q", "-am", "main moves on")
    git(repo, "checkout", "-q", "feature")
    assert merge_base(repo, "main") == start


def subprocess_out(repo: pathlib.Path, *args: str) -> str:
    return str(
        run(
            [GIT, *args],
            cwd=repo,
            env=session.git_env(dict(os.environ)),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    ).strip()


def test_none_arm_deletes_a_skill_and_drops_its_preloads(
    repo: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    agents = repo / "plugins" / "demo" / "agents"
    agents.mkdir()
    (agents / "reviewer.md").write_text(
        "---\nname: reviewer\ndescription: Reviews.\nskills:\n  - s\n  - other\n---\n\nYou review.\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "agent")
    store = tmp_path / "store"
    none = none_arm(old_arm(repo, "main", store), "demo:s", store)
    root = pathlib.Path(none.plugins["demo"])
    assert not (root / "skills" / "s").exists()
    assert (
        (root / "agents" / "reviewer.md").read_text()
        == "---\nname: reviewer\ndescription: Reviews.\nskills:\n  - other\n---\n\nYou review.\n"
    )
    assert none.name == "none"


def test_none_arm_cuts_an_agents_body_to_its_first_line(
    repo: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    agents = repo / "plugins" / "demo" / "agents"
    agents.mkdir()
    (agents / "reviewer.md").write_text(
        "---\nname: reviewer\ndescription: Reviews.\n---\n\nYou review.\n\n## Rules\n\n- Be strict.\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "agent")
    store = tmp_path / "store"
    none = none_arm(old_arm(repo, "main", store), "demo:reviewer", store)
    text = pathlib.Path(none.plugins["demo"], "agents", "reviewer.md").read_text()
    assert text == "---\nname: reviewer\ndescription: Reviews.\n---\n\nYou review.\n"


def test_none_arm_refuses_an_unknown_target(repo: pathlib.Path, tmp_path: pathlib.Path) -> None:
    store = tmp_path / "store"
    with pytest.raises(ValueError, match="no such skill, agent or command"):
        none_arm(old_arm(repo, "main", store), "demo:missing", store)


def test_a_named_old_arm_is_a_second_arm_from_the_same_ref(
    repo: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    store = tmp_path / "store"
    first, second = old_arm(repo, "main", store), old_arm(repo, "main", store, name="new")
    assert (first.name, second.name, first.hash) == ("old", "new", second.hash)
