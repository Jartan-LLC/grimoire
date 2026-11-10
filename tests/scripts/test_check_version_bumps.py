import json
import os
import pathlib
import subprocess
import sys

import pytest
from script_loader import load_script

vb = load_script("check-version-bumps.py")


def git(repo: pathlib.Path, *args: str) -> str:
    # Fixed git argv in a temporary fixture repository, never this checkout.
    return subprocess.run(  # noqa: S603
        [vb.GIT, "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def commit(repo: pathlib.Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)


def bump(repo: pathlib.Path, name: str, version: str) -> None:
    manifest = repo / "plugins" / name / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"name": name, "version": version}))


def plugin(repo: pathlib.Path, name: str, version: str) -> None:
    bump(repo, name, version)
    (repo / "plugins" / name / "CHANGELOG.md").write_text(f"## {version}\n\n- Shipped.\n")


@pytest.fixture
def repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    # As tests/helpers/fixture.js gitEnv(): a contributor's git settings (autocrlf,
    # hooks, signing) and a leaked GIT_DIR cannot reach the fixture.
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "Fixture")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "fixture@example.com")
    monkeypatch.setattr(vb, "ROOT", tmp_path)
    git(tmp_path, "init", "-q", "-b", "main")
    for name in ("a", "b"):
        plugin(tmp_path, name, "1.0.0")
        (tmp_path / "plugins" / name / "README.md").write_text("x\n")
    commit(tmp_path, "plugins")
    git(tmp_path, "switch", "-qc", "branch")
    return tmp_path


def unbumped_message(name: str) -> str:
    return (
        f"plugins/{name}: changed since main, but its version is still 1.0.0:"
        " bump it in .claude-plugin/plugin.json"
    )


def test_unbumped_names_a_changed_plugin_that_kept_its_version(repo: pathlib.Path) -> None:
    (repo / "plugins" / "a" / "README.md").write_text("y\n")
    commit(repo, "change a")
    assert vb.unbumped("main") == [unbumped_message("a")]


def test_unbumped_passes_a_changed_plugin_with_a_new_version(repo: pathlib.Path) -> None:
    (repo / "plugins" / "a" / "README.md").write_text("y\n")
    bump(repo, "a", "1.0.1")
    commit(repo, "change and bump a")
    assert vb.unbumped("main") == []


def test_unbumped_ignores_a_change_to_the_changelog_alone(repo: pathlib.Path) -> None:
    (repo / "plugins" / "a" / "CHANGELOG.md").write_text("## 1.0.0\n\n- Reworded.\n")
    commit(repo, "reword a's changelog")
    assert vb.unbumped("main") == []


def test_unbumped_counts_a_generated_codex_file(repo: pathlib.Path) -> None:
    codex = repo / "plugins" / "a" / ".codex-plugin" / "plugin.json"
    codex.parent.mkdir()
    codex.write_text("{}\n")
    commit(repo, "regenerate a's Codex manifest")
    assert vb.unbumped("main") == [unbumped_message("a")]


def test_unbumped_counts_an_uncommitted_change(repo: pathlib.Path) -> None:
    (repo / "plugins" / "b" / "README.md").write_text("y\n")
    assert vb.unbumped("main") == [unbumped_message("b")]


def test_unbumped_skips_a_new_and_a_removed_plugin(repo: pathlib.Path) -> None:
    plugin(repo, "new", "0.1.0")
    git(repo, "rm", "-rq", "plugins/b")
    commit(repo, "add new, remove b")
    assert vb.unbumped("main") == []


def test_unbumped_counts_both_plugins_of_a_file_moved_between_them(repo: pathlib.Path) -> None:
    git(repo, "mv", "plugins/a/README.md", "plugins/b/moved.md")
    commit(repo, "move a's README into b")
    assert vb.unbumped("main") == [unbumped_message("a"), unbumped_message("b")]


def test_unbumped_leaves_out_what_the_base_gained_after_the_branch_left(
    repo: pathlib.Path,
) -> None:
    git(repo, "switch", "-q", "main")
    (repo / "plugins" / "a" / "README.md").write_text("y\n")
    bump(repo, "a", "1.0.1")
    commit(repo, "release a 1.0.1")
    git(repo, "switch", "-q", "branch")
    assert vb.unbumped("main") == []


def test_unbumped_fails_a_version_the_base_released_meanwhile(repo: pathlib.Path) -> None:
    # As in CI, where HEAD is the PR's merge commit and the base its first parent.
    git(repo, "switch", "-q", "main")
    bump(repo, "a", "1.0.1")
    commit(repo, "release a 1.0.1")
    git(repo, "switch", "-q", "branch")
    (repo / "plugins" / "a" / "README.md").write_text("y\n")
    bump(repo, "a", "1.0.1")
    commit(repo, "change a, bumping it to the version main took")
    git(repo, "switch", "-q", "--detach", "main")
    git(repo, "merge", "-q", "--no-edit", "branch")
    assert vb.unbumped("HEAD^1") == [
        "plugins/a: changed since HEAD^1, but its version is still 1.0.1:"
        " bump it in .claude-plugin/plugin.json"
    ]


def test_main_fails_an_unbumped_plugin_and_a_base_it_cannot_find(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "plugins" / "a" / "README.md").write_text("y\n")
    monkeypatch.setattr(sys, "argv", ["check-version-bumps.py", "--base", "main"])
    assert vb.main() == 1
    assert capsys.readouterr().out == f"{unbumped_message('a')}\n"
    monkeypatch.setattr(sys, "argv", ["check-version-bumps.py", "--base", "no-such-ref"])
    assert vb.main() == 1
    out = capsys.readouterr().out
    assert out.startswith("--base no-such-ref: no merge base with HEAD (")
    assert out.endswith("; pass a ref this checkout has, such as origin/main (make: BASE=<ref>)\n")


def test_main_fails_an_empty_base(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # `make verify BASE=` passes an empty ref; skipping the check would pass silently.
    monkeypatch.setattr(sys, "argv", ["check-version-bumps.py", "--base", ""])
    assert vb.main() == 1
    assert capsys.readouterr().out.startswith("--base : no merge base with HEAD (")
