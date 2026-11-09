import json
import pathlib
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
