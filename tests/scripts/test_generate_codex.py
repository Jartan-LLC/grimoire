import pathlib
import re
import tomllib

import pytest
from script_loader import load_script

gc = load_script("generate-codex.py")
PATH = pathlib.Path("agents/demo.md")


def frontmatter(*lines: str, body: str = "Body.") -> str:
    return "\n".join(["---", *lines, "---", "", body, ""])


def test_parse_frontmatter_reads_scalars_lists_and_body() -> None:
    text = frontmatter(
        "name: demo",
        "description: Does a: thing -- with detail",
        "# a comment",
        "  # an indented comment",
        "",
        "skills:",
        "  - code-hygiene",
        "  - gitwise:github-conventions",
        "tools:",
        body="First line.\n\nSecond line.",
    )
    fields, body = gc.parse_frontmatter(text, PATH)
    assert fields == {
        "name": "demo",
        "description": "Does a: thing -- with detail",
        "skills": ["code-hygiene", "gitwise:github-conventions"],
        "tools": [],
    }
    assert body == "First line.\n\nSecond line."


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("name: demo\n---\nBody\n", "expected frontmatter to open with ---"),
        ("---\nname: demo\nBody\n", "frontmatter has no closing ---"),
        (frontmatter('name: "demo"'), "'name' must be a plain unquoted value"),
        (frontmatter("name: 'demo'"), "'name' must be a plain unquoted value"),
        (frontmatter("description: >", "  folded"), "'description' must be a plain unquoted value"),
        (
            frontmatter("description: |", "  literal"),
            "'description' must be a plain unquoted value",
        ),
        (frontmatter("skills: [a, b]"), "'skills' must be a plain unquoted value"),
        (frontmatter("meta: {a: b}"), "'meta' must be a plain unquoted value"),
        (
            frontmatter("name: demo", "just some words"),
            "unsupported frontmatter line 'just some words'",
        ),
        (frontmatter("model2: x"), "unsupported frontmatter line 'model2: x'"),
        (
            frontmatter("  - orphan item", "name: demo"),
            "unsupported frontmatter line '  - orphan item'",
        ),
        (frontmatter("name: demo", "  - extra"), "'name' has both a value and list items"),
    ],
)
def test_parse_frontmatter_rejects_what_it_would_misread(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=rf"^{re.escape(str(PATH))}: .*{re.escape(message)}"):
        gc.parse_frontmatter(text, PATH)


@pytest.mark.xfail(
    strict=True,
    reason="grimoire#79: a trailing ' # comment' is kept as part of the value; YAML, which Claude Code reads, drops it",
)
def test_parse_frontmatter_does_not_keep_an_inline_comment_in_the_value() -> None:
    try:
        fields, _ = gc.parse_frontmatter(frontmatter("name: demo # the reviewer"), PATH)
    except ValueError:
        return
    assert fields["name"] == "demo"


@pytest.mark.xfail(
    strict=True,
    reason="grimoire#80: quoting is rejected on key values but not on list items, which keep their quotes",
)
def test_parse_frontmatter_does_not_keep_quotes_on_a_list_item() -> None:
    try:
        fields, _ = gc.parse_frontmatter(frontmatter("skills:", '  - "code-hygiene"'), PATH)
    except ValueError:
        return
    assert fields["skills"] == ["code-hygiene"]


@pytest.mark.parametrize(
    "value",
    [
        "plain",
        r"C:\path\to\file",
        r"\b is not a backspace",
        'say "hi"',
        "trailing backslash \\",
        "line one\nline two\r\n\ttabbed",
        "".join(chr(c) for c in range(0x80)),
        "na\u00efve \u2014 \U0001f600",
    ],
)
def test_basic_string_round_trips_through_toml(value: str) -> None:
    rendered = gc.basic_string(value)
    assert "\n" not in rendered
    assert tomllib.loads(f"v = {rendered}")["v"] == value


def render(*lines: str, body: str = "Body.", plugin: str = "praxis") -> dict[str, object]:
    fields, parsed_body = gc.parse_frontmatter(frontmatter(*lines, body=body), PATH)
    return tomllib.loads(gc.render_agent_toml(fields, parsed_body, plugin))


def test_render_agent_toml_keeps_name_description_and_body_verbatim() -> None:
    body = r'Match \d+ and "quotes"; a path C:\temp; a trailing quote: ' + "'"
    role = render("name: demo", r"description: Reviews C:\code and \n escapes", body=body)
    assert role == {
        "name": "demo",
        "description": r"Reviews C:\code and \n escapes",
        "developer_instructions": body + "\n",
    }


def test_render_agent_toml_names_the_skills_qualified_by_plugin() -> None:
    role = render(
        "name: demo",
        "description: d",
        "skills:",
        "  - code-hygiene",
        "  - gitwise:github-conventions",
    )
    assert role["developer_instructions"] == (
        "Body.\n\n## Skills\n\n"
        "Load these skills before starting: `praxis:code-hygiene`, `gitwise:github-conventions`.\n"
    )


@pytest.mark.parametrize(
    ("mode", "sandbox"),
    [("plan", "read-only"), ("readOnly", "read-only"), ("acceptEdits", "workspace-write")],
)
def test_render_agent_toml_maps_permission_mode_to_sandbox(mode: str, sandbox: str) -> None:
    role = render("name: demo", "description: d", f"permissionMode: {mode}")
    assert role["sandbox_mode"] == sandbox


@pytest.mark.parametrize("lines", [(), ("permissionMode: default",), ("permissionMode: bypass",)])
def test_render_agent_toml_emits_no_sandbox_for_an_unmapped_mode(lines: tuple[str, ...]) -> None:
    assert "sandbox_mode" not in render("name: demo", "description: d", *lines)


def test_render_agent_toml_drops_fields_codex_would_reject() -> None:
    role = render("name: demo", "description: d", "model: opus", "tools: Read, Grep", "color: blue")
    assert set(role) == {"name", "description", "developer_instructions"}


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        (("description: d",), "frontmatter 'name' must be a single non-empty value"),
        (("name:", "description: d"), "frontmatter 'name' must be a single non-empty value"),
        (
            ("name:", "  - a", "description: d"),
            "frontmatter 'name' must be a single non-empty value",
        ),
        (("name: demo",), "frontmatter 'description' must be a single non-empty value"),
        (
            ("name: demo", "description: d", "skills: code-hygiene"),
            "frontmatter 'skills' must be a list",
        ),
    ],
)
def test_render_agent_toml_rejects_malformed_fields(lines: tuple[str, ...], message: str) -> None:
    fields, body = gc.parse_frontmatter(frontmatter(*lines), PATH)
    with pytest.raises(ValueError, match=re.escape(message)):
        gc.render_agent_toml(fields, body, "praxis")


def test_render_agent_toml_rejects_a_body_that_would_close_the_literal() -> None:
    fields, body = gc.parse_frontmatter(
        frontmatter("name: demo", "description: d", body="a ''' b"), PATH
    )
    with pytest.raises(ValueError, match="body contains '''"):
        gc.render_agent_toml(fields, body, "praxis")


def touch(root: pathlib.Path, *relatives: str, contents: str = "") -> None:
    for relative in relatives:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)


def test_find_orphans_reports_every_generated_file_no_longer_produced(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gc, "ROOT", tmp_path)
    monkeypatch.setattr(
        gc, "CODEX_MARKETPLACE", tmp_path / ".agents" / "plugins" / "marketplace.json"
    )
    expected = [
        ".agents/plugins/marketplace.json",
        "plugins/kept/.codex-plugin/plugin.json",
        "plugins/kept/codex/agents/live.toml",
    ]
    orphans = [
        ".agents/plugins/notes.txt",
        "plugins/kept/.codex-plugin/stray.json",
        "plugins/kept/codex/agents/deleted-agent.toml",
        "plugins/no-agents-now/codex/agents/old.toml",
        "plugins/left-marketplace/.codex-plugin/plugin.json",
    ]
    touch(tmp_path, *expected, *orphans, "plugins/kept/agents/live.md", "plugins/kept/README.md")
    (tmp_path / "plugins/kept/codex/agents/nested-dir").mkdir()

    targets = [(tmp_path / relative, "") for relative in expected]
    assert gc.find_orphans(targets) == sorted(pathlib.Path(o) for o in orphans)


def test_find_orphans_is_empty_when_every_file_is_a_target(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gc, "ROOT", tmp_path)
    monkeypatch.setattr(
        gc, "CODEX_MARKETPLACE", tmp_path / ".agents" / "plugins" / "marketplace.json"
    )
    expected = [".agents/plugins/marketplace.json", "plugins/p/codex/agents/a.toml"]
    touch(tmp_path, *expected)
    assert gc.find_orphans([(tmp_path / relative, "") for relative in expected]) == []


def test_find_divergent_copies_lists_every_copy_once_one_differs(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gc, "ROOT", tmp_path)
    monkeypatch.setattr(gc, "DUPLICATED_HOOK_SCRIPTS", ["hooks/scripts/shared.js"])
    touch(
        tmp_path,
        "plugins/a/hooks/scripts/shared.js",
        "plugins/c/hooks/scripts/shared.js",
        contents="same",
    )
    touch(tmp_path, "plugins/b/hooks/scripts/shared.js", contents="same ")
    assert gc.find_divergent_copies() == [
        pathlib.Path("plugins/a/hooks/scripts/shared.js"),
        pathlib.Path("plugins/b/hooks/scripts/shared.js"),
        pathlib.Path("plugins/c/hooks/scripts/shared.js"),
    ]


@pytest.mark.parametrize("plugins", [("a", "b"), ("a",), ()])
def test_find_divergent_copies_is_empty_while_copies_match(
    plugins: tuple[str, ...], tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gc, "ROOT", tmp_path)
    monkeypatch.setattr(gc, "DUPLICATED_HOOK_SCRIPTS", ["hooks/scripts/shared.js"])
    touch(tmp_path, *(f"plugins/{p}/hooks/scripts/shared.js" for p in plugins), contents="same")
    assert gc.find_divergent_copies() == []
