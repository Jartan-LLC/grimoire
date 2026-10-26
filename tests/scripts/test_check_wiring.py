import json
import pathlib

import pytest
from script_loader import load_script

cw = load_script("check-wiring.py")


def plugin(root: pathlib.Path, name: str, dependencies: list[object] | None = None) -> pathlib.Path:
    manifest: dict[str, object] = {"name": name, "version": "1.0.0"}
    if dependencies is not None:
        manifest["dependencies"] = dependencies
    path = root / "plugins" / name
    (path / ".claude-plugin").mkdir(parents=True)
    (path / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest))
    return path


def skill(
    plugin_dir: pathlib.Path, name: str, body: str = "", frontmatter: str | None = None
) -> None:
    path = plugin_dir / "skills" / name
    path.mkdir(parents=True)
    head = frontmatter if frontmatter is not None else f"name: {name}\ndescription: Does {name}."
    (path / "SKILL.md").write_text(f"---\n{head}\n---\n\n{body}\n")


def agent(plugin_dir: pathlib.Path, name: str, skills: list[str], body: str = "") -> None:
    path = plugin_dir / "agents"
    path.mkdir(parents=True, exist_ok=True)
    entries = "".join(f"  - {entry}\n" for entry in skills)
    (path / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: Reviews.\nskills:\n{entries}---\n\n{body}\n"
    )


@pytest.fixture
def tree(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """`lib` with one skill, and `app`, which declares `lib`."""
    monkeypatch.setattr(cw, "ROOT", tmp_path)
    skill(plugin(tmp_path, "lib"), "conventions")
    skill(plugin(tmp_path, "app", [{"name": "lib", "version": "^1.0.0"}]), "helper")
    return tmp_path


def test_problems_is_empty_when_every_pointer_resolves_within_dependencies(
    tree: pathlib.Path,
) -> None:
    app = tree / "plugins" / "app"
    agent(app, "reviewer", ["helper", "lib:conventions"], "Load the `lib:conventions` skill.")
    skill(app, "flow", "Then run `app:reviewer`, as lib does.")
    (app / "hooks").mkdir()
    (app / "hooks" / "hooks.json").write_text('{"context": "Load the lib:conventions skill."}')
    assert cw.problems() == []


def test_problems_fails_when_no_plugin_is_found(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cw, "ROOT", tmp_path)
    assert cw.problems() == ["no plugins/*/.claude-plugin/plugin.json found -- nothing was checked"]


def test_problems_names_an_agent_skills_entry_that_names_no_skill(tree: pathlib.Path) -> None:
    agent(tree / "plugins" / "app", "reviewer", ["missing", "lib:absent"])
    assert cw.problems() == [
        "plugins/app/agents/reviewer.md: app:missing names no skill",
        "plugins/app/agents/reviewer.md: lib:absent names no skill",
    ]


def test_problems_names_a_body_pointer_that_names_nothing(tree: pathlib.Path) -> None:
    skill(tree / "plugins" / "app", "flow", "Load the `lib:convention` skill.")
    assert cw.problems() == [
        "plugins/app/skills/flow/SKILL.md: lib:convention names no skill, agent or command"
    ]


def test_problems_names_a_pointer_into_an_undeclared_plugin(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cw, "ROOT", tmp_path)
    skill(plugin(tmp_path, "lib"), "conventions")
    app = plugin(tmp_path, "app")
    agent(app, "reviewer", ["lib:conventions"])
    skill(app, "flow", "Load the `lib:conventions` skill.")
    assert cw.problems() == [
        "plugins/app/skills/flow/SKILL.md: lib:conventions is in lib, which app does not declare",
        "plugins/app/agents/reviewer.md: lib:conventions is in lib, which app does not declare",
    ]


def test_problems_names_a_skills_entry_for_an_undeclared_plugin_outside_the_tree(
    tree: pathlib.Path,
) -> None:
    agent(tree / "plugins" / "app", "reviewer", ["elsewhere:thing"])
    assert cw.problems() == [
        "plugins/app/agents/reviewer.md: elsewhere:thing is in elsewhere, which app does not declare"
    ]


def test_problems_accepts_a_skills_entry_for_a_declared_plugin_outside_the_tree(
    tree: pathlib.Path,
) -> None:
    app = plugin(tree, "other", ["elsewhere@market"])
    agent(app, "reviewer", ["elsewhere:thing"])
    assert cw.problems() == []


def test_problems_names_a_bare_mention_of_an_undeclared_plugin(tree: pathlib.Path) -> None:
    skill(tree / "plugins" / "lib", "notes", "Pairs well with app.")
    assert cw.problems() == [
        "plugins/lib/skills/notes/SKILL.md: names app, which lib does not declare"
    ]


def test_problems_checks_frontmatter_values_and_hooks(tree: pathlib.Path) -> None:
    lib = tree / "plugins" / "lib"
    skill(lib, "notes", frontmatter="name: notes\ndescription: Use with app:helper.")
    (lib / "hooks").mkdir()
    agent(lib, "checker", [])
    (lib / "hooks" / "hooks.json").write_text(
        '{"context": "Load the lib:nothing skill, or spawn lib:checker."}'
    )
    assert cw.problems() == [
        "plugins/lib/skills/notes/SKILL.md: app:helper is in app, which lib does not declare",
        "plugins/lib/hooks/hooks.json: lib:nothing names no skill, agent or command",
    ]


def test_problems_names_a_mismatched_name_and_a_missing_description(tree: pathlib.Path) -> None:
    lib = tree / "plugins" / "lib"
    skill(lib, "notes", frontmatter="name: note\ndescription: Notes.")
    skill(lib, "bare", frontmatter="name: bare")
    assert cw.problems() == [
        "plugins/lib/skills/bare/SKILL.md: no description",
        "plugins/lib/skills/notes/SKILL.md: name 'note' differs from 'notes'",
    ]


def test_problems_reports_frontmatter_that_does_not_parse(tree: pathlib.Path) -> None:
    skill(tree / "plugins" / "lib", "notes", frontmatter='name: notes\ndescription: "Quoted."')
    assert cw.problems() == [
        "plugins/lib/skills/notes/SKILL.md: frontmatter 'description' must be a plain unquoted value"
    ]


def test_main_exits_nonzero_and_prints_each_problem(
    tree: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    skill(tree / "plugins" / "app", "flow", "Load `app:nothing`.")
    assert cw.main() == 1
    assert capsys.readouterr().out == (
        "plugins/app/skills/flow/SKILL.md: app:nothing names no skill, agent or command\n"
    )
