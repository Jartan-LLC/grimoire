import json
import os
import pathlib
import subprocess
import sys

import pytest
from script_loader import load_script

cc = load_script("check-changelogs.py")

CHANGELOG = """# Changelog

## 1.2.0

- New skill.

### Upgrading

- Re-run the installer.

## 1.1.10

- Ten.

## 1.1.1

- One.

## 1.1.0
"""


def test_section_is_the_text_up_to_the_next_level_two_heading() -> None:
    assert (
        cc.section(CHANGELOG, "1.2.0") == "- New skill.\n\n### Upgrading\n\n- Re-run the installer."
    )


def test_section_matches_the_whole_version_not_a_prefix() -> None:
    assert cc.section(CHANGELOG, "1.1.1") == "- One."
    assert cc.section(CHANGELOG, "1.1.10") == "- Ten."
    assert cc.section(CHANGELOG, "1.1") == ""


def test_section_is_empty_for_a_missing_or_bodiless_entry() -> None:
    assert cc.section(CHANGELOG, "9.9.9") == ""
    assert cc.section(CHANGELOG, "1.1.0") == ""


def test_section_runs_to_the_end_of_the_file() -> None:
    assert cc.section("## 2.0.0\n\n- Last.\n", "2.0.0") == "- Last."


def test_section_ignores_trailing_whitespace_on_the_heading() -> None:
    assert cc.section("## 2.0.0  \n\n- Last.\n", "2.0.0") == "- Last."


def test_section_does_not_match_a_heading_with_more_than_the_version() -> None:
    assert cc.section("## 2.0.0 - 2026-10-12\n\n- Last.\n", "2.0.0") == ""


HEADING = " heading (the version alone, matching plugin.json)"


def plugin(root: pathlib.Path, name: str, version: str | None, changelog: str | None) -> None:
    manifest = root / "plugins" / name / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    fields = {"name": name} if version is None else {"name": name, "version": version}
    manifest.write_text(json.dumps(fields))
    if changelog is not None:
        (root / "plugins" / name / "CHANGELOG.md").write_text(changelog)


def test_problems_names_each_plugin_without_a_current_entry(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    plugin(tmp_path, "current", "1.0.0", "## 1.0.0\n\n- Shipped.\n")
    plugin(tmp_path, "behind", "1.1.0", "## 1.0.0\n\n- Shipped.\n")
    plugin(tmp_path, "bodiless", "2.0.0", "## 2.0.0\n\n## 1.0.0\n\n- Old.\n")
    plugin(tmp_path, "missing", "1.0.0", None)
    plugin(tmp_path, "unversioned", None, "## 1.0.0\n\n- Shipped.\n")
    assert cc.problems() == [
        f"plugins/behind/CHANGELOG.md: no entry under a '## 1.1.0'{HEADING}",
        f"plugins/bodiless/CHANGELOG.md: no entry under a '## 2.0.0'{HEADING}",
        "plugins/missing: no CHANGELOG.md",
        "plugins/unversioned/.claude-plugin/plugin.json: no version",
    ]


def test_problems_fails_when_no_plugin_is_found(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    assert cc.problems() == ["no plugins/*/.claude-plugin/plugin.json found -- nothing was checked"]


def test_problems_is_empty_when_every_plugin_is_current(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    plugin(tmp_path, "a", "1.0.0", "## 1.0.0\n\n- A.\n")
    plugin(tmp_path, "b", "0.1.0", "## 0.1.0\n\n- B.\n")
    assert cc.problems() == []


def test_notes_prints_the_entry(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    plugin(tmp_path, "demo", "1.2.0", CHANGELOG)
    monkeypatch.setattr(sys, "argv", ["check-changelogs.py", "--notes", "demo", "1.1.1"])
    assert cc.main() == 0
    assert capsys.readouterr() == ("- One.\n", "")


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (("demo", "3.0.0"), f"plugins/demo/CHANGELOG.md: no entry under a '## 3.0.0'{HEADING}"),
        (("demo", "1.1.0"), f"plugins/demo/CHANGELOG.md: no entry under a '## 1.1.0'{HEADING}"),
        (("absent", "1.0.0"), "plugins/absent: no CHANGELOG.md"),
    ],
)
def test_notes_fails_without_an_entry(
    args: tuple[str, str],
    message: str,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    plugin(tmp_path, "demo", "1.2.0", CHANGELOG)
    monkeypatch.setattr(sys, "argv", ["check-changelogs.py", "--notes", *args])
    assert cc.main() == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"{message}\n"


@pytest.mark.parametrize(
    ("constraint", "version", "verdict"),
    [
        ("^1.2.0", "1.2.0", True),
        ("^1.2.0", "1.9.3", True),
        ("^1.2.0", "2.0.0", False),
        ("^1.2.0", "1.1.9", False),
        ("^0.3.1", "0.3.9", True),
        ("^0.3.1", "0.4.0", False),
        ("~1.2.0", "1.2.7", True),
        ("~1.2.0", "1.3.0", False),
        ("1.2.0", "1.2.0", True),
        ("1.2.0", "1.2.1", False),
        ("=1.2.0", "1.2.0", True),
        ("^0.0.3", "0.0.3", True),
        ("^0.0.3", "0.0.4", False),
        ("^2.0.0", "2.0.0-rc1", False),
        ("^1.2.0", "1.3.0-rc.1", False),
        ("1.2.0", "1.2.0-rc1", False),
        ("^2.0.0-0", "2.0.0-rc1", None),
        ("^2.0.0-0", "2.0.0", True),
        (">=1.0.0", "1.2.0", None),
        ("^1.2", "1.2.0", None),
        ("", "1.2.0", None),
        ("=1.2.3-rc1", "1.2.3", False),
        ("1.2.3-rc1", "1.2.3", False),
        ("^01.2.3", "1.2.3", None),
        ("1.2.3", "01.2.3", None),
        ("^1.2.0", "1.2.0+build.5", None),
    ],
)
def test_accepts_reads_caret_tilde_and_exact_ranges(
    constraint: str, version: str, verdict: bool | None
) -> None:
    assert cc.accepts(constraint, version) is verdict


def test_problems_names_a_directory_named_unlike_its_manifest(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    plugin(tmp_path, "dir", "1.0.0", "## 1.0.0\n\n- Shipped.\n")
    manifest = tmp_path / "plugins" / "dir" / ".claude-plugin" / "plugin.json"
    manifest.write_text(json.dumps({"name": "other", "version": "1.0.0"}))
    assert cc.problems() == [
        "plugins/dir/.claude-plugin/plugin.json: name 'other' differs from its directory"
    ]


def test_problems_names_a_dependency_range_the_tree_does_not_meet(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    plugin(tmp_path, "base", "1.2.0", "## 1.2.0\n\n- Shipped.\n")
    plugin(tmp_path, "app", "1.0.0", "## 1.0.0\n\n- Shipped.\n")
    manifest = tmp_path / "plugins" / "app" / ".claude-plugin" / "plugin.json"
    deps = [
        {"name": "base", "version": "^1.3.0"},
        {"name": "elsewhere", "version": "^9.0.0"},
        {"name": "base", "version": "^9.0.0", "marketplace": "other"},
        "base",
        {"version": "^1.0.0"},
    ]
    manifest.write_text(json.dumps({"name": "app", "version": "1.0.0", "dependencies": deps}))
    where = "plugins/app/.claude-plugin/plugin.json"
    assert cc.problems() == [
        f"{where}: needs base ^1.3.0, but base here is 1.2.0",
        f"{where}: needs elsewhere, which is not a plugin here",
        f"{where}: a dependency that is neither a name nor an object with one",
    ]


def test_problems_names_a_dependency_this_marketplace_lacks(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text(json.dumps({"name": "home"}))
    plugin(tmp_path, "base", "1.2.0", "## 1.2.0\n\n- Shipped.\n")
    plugin(tmp_path, "app", "1.0.0", "## 1.0.0\n\n- Shipped.\n")
    manifest = tmp_path / "plugins" / "app" / ".claude-plugin" / "plugin.json"
    deps = [
        "bsae",
        "absent@home",
        "far@away",
        {"name": "gone", "marketplace": "home"},
        {"name": "far", "marketplace": "away"},
        "base",
        "base@home",
    ]
    manifest.write_text(json.dumps({"name": "app", "version": "1.0.0", "dependencies": deps}))
    where = "plugins/app/.claude-plugin/plugin.json"
    assert cc.problems() == [
        f"{where}: needs bsae, which is not a plugin here",
        f"{where}: needs absent, which is not a plugin here",
        f"{where}: needs gone, which is not a plugin here",
    ]


@pytest.mark.parametrize(
    ("dependencies", "message"),
    [
        ({"name": "base", "version": "^9.0.0"}, "dependencies is not a list"),
        ("base", "dependencies is not a list"),
        (
            [{"name": "base", "version": ">=1.0.0"}],
            "cannot check the range '>=1.0.0' for base 1.2.0",
        ),
        ([{"name": "base", "version": 1}], "the version range for base is not a string"),
        ([{"name": "base", "version": None}], "the version range for base is not a string"),
    ],
)
def test_problems_names_dependencies_it_cannot_check(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, dependencies: object, message: str
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    plugin(tmp_path, "base", "1.2.0", "## 1.2.0\n\n- Shipped.\n")
    plugin(tmp_path, "app", "1.0.0", "## 1.0.0\n\n- Shipped.\n")
    manifest = tmp_path / "plugins" / "app" / ".claude-plugin" / "plugin.json"
    manifest.write_text(
        json.dumps({"name": "app", "version": "1.0.0", "dependencies": dependencies})
    )
    assert cc.problems() == [f"plugins/app/.claude-plugin/plugin.json: {message}"]


def test_problems_checks_a_range_that_names_this_marketplace(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text(json.dumps({"name": "home"}))
    plugin(tmp_path, "base", "1.2.0", "## 1.2.0\n\n- Shipped.\n")
    plugin(tmp_path, "app", "1.0.0", "## 1.0.0\n\n- Shipped.\n")
    manifest = tmp_path / "plugins" / "app" / ".claude-plugin" / "plugin.json"
    deps = [
        {"name": "base", "version": "^9.0.0", "marketplace": "home"},
        {"name": "base", "version": "^9.0.0", "marketplace": "away"},
    ]
    manifest.write_text(json.dumps({"name": "app", "version": "1.0.0", "dependencies": deps}))
    assert cc.problems() == [
        "plugins/app/.claude-plugin/plugin.json: needs base ^9.0.0, but base here is 1.2.0"
    ]


def git(repo: pathlib.Path, *args: str) -> str:
    # Fixed git argv in a temporary fixture repository, never this checkout.
    return subprocess.run(  # noqa: S603
        [cc.GIT, "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def commit(repo: pathlib.Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)


def bump(repo: pathlib.Path, name: str, version: str) -> None:
    manifest = repo / "plugins" / name / ".claude-plugin" / "plugin.json"
    manifest.write_text(json.dumps({"name": name, "version": version}))


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
    monkeypatch.setattr(cc, "ROOT", tmp_path)
    git(tmp_path, "init", "-q", "-b", "main")
    for name in ("a", "b"):
        plugin(tmp_path, name, "1.0.0", "## 1.0.0\n\n- Shipped.\n")
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
    assert cc.unbumped("main") == [unbumped_message("a")]


def test_unbumped_passes_a_changed_plugin_with_a_new_version(repo: pathlib.Path) -> None:
    (repo / "plugins" / "a" / "README.md").write_text("y\n")
    bump(repo, "a", "1.0.1")
    commit(repo, "change and bump a")
    assert cc.unbumped("main") == []


def test_unbumped_ignores_a_change_to_the_changelog_alone(repo: pathlib.Path) -> None:
    (repo / "plugins" / "a" / "CHANGELOG.md").write_text("## 1.0.0\n\n- Reworded.\n")
    commit(repo, "reword a's changelog")
    assert cc.unbumped("main") == []


def test_unbumped_counts_a_generated_codex_file(repo: pathlib.Path) -> None:
    codex = repo / "plugins" / "a" / ".codex-plugin" / "plugin.json"
    codex.parent.mkdir()
    codex.write_text("{}\n")
    commit(repo, "regenerate a's Codex manifest")
    assert cc.unbumped("main") == [unbumped_message("a")]


def test_unbumped_counts_an_uncommitted_change(repo: pathlib.Path) -> None:
    (repo / "plugins" / "b" / "README.md").write_text("y\n")
    assert cc.unbumped("main") == [unbumped_message("b")]


def test_unbumped_skips_a_new_and_a_removed_plugin(repo: pathlib.Path) -> None:
    plugin(repo, "new", "0.1.0", "## 0.1.0\n\n- First.\n")
    git(repo, "rm", "-rq", "plugins/b")
    commit(repo, "add new, remove b")
    assert cc.unbumped("main") == []


def test_unbumped_counts_both_plugins_of_a_file_moved_between_them(repo: pathlib.Path) -> None:
    git(repo, "mv", "plugins/a/README.md", "plugins/b/moved.md")
    commit(repo, "move a's README into b")
    assert cc.unbumped("main") == [unbumped_message("a"), unbumped_message("b")]


def test_unbumped_leaves_out_what_the_base_gained_after_the_branch_left(
    repo: pathlib.Path,
) -> None:
    git(repo, "switch", "-q", "main")
    (repo / "plugins" / "a" / "README.md").write_text("y\n")
    bump(repo, "a", "1.0.1")
    commit(repo, "release a 1.0.1")
    git(repo, "switch", "-q", "branch")
    assert cc.unbumped("main") == []


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
    assert cc.unbumped("HEAD^1") == [
        "plugins/a: changed since HEAD^1, but its version is still 1.0.1:"
        " bump it in .claude-plugin/plugin.json"
    ]


def test_main_with_base_fails_an_unbumped_plugin_and_a_base_it_cannot_find(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "plugins" / "a" / "README.md").write_text("y\n")
    monkeypatch.setattr(sys, "argv", ["check-changelogs.py", "--base", "main"])
    assert cc.main() == 1
    assert capsys.readouterr().out == f"{unbumped_message('a')}\n"
    monkeypatch.setattr(sys, "argv", ["check-changelogs.py", "--base", "no-such-ref"])
    assert cc.main() == 1
    out = capsys.readouterr().out
    assert out.startswith("--base no-such-ref: no merge base with HEAD (")
    assert out.endswith("; pass a ref this checkout has, such as origin/main (make: BASE=<ref>)\n")


def test_main_fails_an_empty_base(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # `make verify BASE=` passes an empty ref; skipping the bump check would pass silently.
    monkeypatch.setattr(sys, "argv", ["check-changelogs.py", "--base", ""])
    assert cc.main() == 1
    assert capsys.readouterr().out.startswith("--base : no merge base with HEAD (")
