#!/usr/bin/env python3
"""Generate the Codex artifacts from the Claude Code sources.

Source of truth is `.claude-plugin/marketplace.json`, each plugin's
`.claude-plugin/plugin.json`, and each plugin's `agents/*.md`. This writes:

    plugins/<name>/.codex-plugin/plugin.json    Codex plugin manifest
    .agents/plugins/marketplace.json            Codex marketplace catalog
    plugins/<name>/codex/agents/*.toml          Codex agent roles

Codex already reads the `.claude-plugin/` paths as a compatibility fallback, so
the manifests are not what makes the marketplace work -- they make it
first-class, carry the `interface` block Codex renders, and survive that
fallback going away.

The agent roles exist because Codex has no plugin-level agent surface at all:
a plugin manifest can point at skills, MCP servers, apps and hooks, and nothing
else. The roles are instead synced into the user's Codex config by each plugin's
SessionStart hook (see hooks/scripts/sync-codex-agents.js).

Run after changing a plugin's name, version, description, keywords, category, or
any agent. `--check` exits non-zero if the generated files are stale, for CI.
"""

import argparse
import json
import pathlib
import re
import sys
from typing import Any

type Json = dict[str, Any]
type Frontmatter = dict[str, str | list[str]]
type Target = tuple[pathlib.Path, str]

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"

# Codex deserializes agent roles with `deny_unknown_fields`, so anything it does
# not understand breaks the whole file rather than being ignored. Only `name`,
# `description`, `nickname_candidates` and valid config keys may appear -- which
# is why our `model`, `tools` and `color` are dropped rather than passed
# through: Codex has no per-agent tool allowlist, and `opus`/`sonnet` are not
# Codex model ids.
#
# Codex's own migrator (external-agent-migration/src/subagents.rs) maps only
# `acceptEdits` and `readOnly`, returning None for `plan`. Emitting nothing
# there would let a plan-mode reviewer inherit a writable sandbox, so `plan` is
# mapped to the mode that actually matches its intent.
PERMISSION_MODE_TO_SANDBOX = {
    "plan": "read-only",
    "readOnly": "read-only",
    "acceptEdits": "workspace-write",
}

# Shipped once per plugin because plugins install independently; kept identical.
DUPLICATED_HOOK_SCRIPTS = ["hooks/scripts/sync-codex-agents.js"]


def display_name(name: str) -> str:
    """Codex renders this in the plugin browser; our names are single words."""
    return name[:1].upper() + name[1:]


def short_description(description: str) -> str:
    """Lead clause of our `<summary> -- <detail>` description convention."""
    return description.split(" -- ", maxsplit=1)[0].strip()


def parse_frontmatter(text: str, path: pathlib.Path) -> tuple[Frontmatter, str]:
    """Split a Markdown document into its YAML frontmatter and body.

    Deliberately minimal: our agent frontmatter is single-line scalars plus a
    `skills:` list, so a YAML dependency would buy nothing. `path` is carried
    only so a malformed file names itself -- otherwise a bare ValueError from
    here points a reader at the generator rather than the file to fix.
    """
    lines = text.split("\n")
    if lines[0].strip() != "---":
        raise ValueError(f"{path}: expected frontmatter to open with ---")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError(f"{path}: frontmatter has no closing ---") from None
    fields: Frontmatter = {}
    key = ""

    for line in lines[1:end]:
        item = re.match(r"\s+-\s+(.*)$", line)
        if item and key:
            values = fields[key]
            if isinstance(values, str):
                raise ValueError(f"{path}: {key} has both a value and list items")
            values.append(item.group(1).strip())
            continue
        match = re.match(r"([A-Za-z_-]+):\s*(.*)$", line)
        if match:
            key = match.group(1)
            fields[key] = match.group(2).strip() or []

    return fields, "\n".join(lines[end + 1 :]).strip()


def scalar(fields: Frontmatter, key: str) -> str:
    """The single-line value of a frontmatter key, which must be present and non-empty."""
    value = fields.get(key)
    if not isinstance(value, str):
        raise ValueError(f"frontmatter {key!r} must be a single non-empty value")
    return value


def qualify(skill: str, plugin: str) -> str:
    """Codex namespaces plugin skills as `plugin:skill`, same as Claude Code."""
    return skill if ":" in skill else f"{plugin}:{skill}"


def basic_string(value: str) -> str:
    r"""Quote a value as a TOML basic string.

    Basic strings process escapes, so an unescaped backslash silently corrupts
    the value (`\b` becomes a backspace) and an unescaped quote ends the string
    early. Control characters are rejected outright by the format. Any of them is
    worse than it sounds: Codex parses role files with `deny_unknown_fields`, so
    a malformed line takes down the whole role rather than the one field.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    for char, shorthand in (("\n", "\\n"), ("\r", "\\r"), ("\t", "\\t"), ("\x7f", "\\u007F")):
        escaped = escaped.replace(char, shorthand)
    # Whatever C0 remains has no shorthand and has to go out as \uXXXX.
    escaped = "".join(c if c >= " " else f"\\u{ord(c):04X}" for c in escaped)
    return f'"{escaped}"'


def render_agent_toml(fields: Frontmatter, body: str, plugin: str) -> str:
    """Render one Claude Code agent as a Codex agent role.

    `skills:` has no Codex equivalent, so the preloaded skills are named in the
    instructions instead. Dropping them silently would strip the reviewers of
    their severity model and conventions -- the grounding that makes findings
    land the same tier whoever raises them.
    """
    name = scalar(fields, "name")
    skills = fields.get("skills", [])
    if isinstance(skills, str):
        raise ValueError("frontmatter 'skills' must be a list, not a single value")
    instructions = body
    if skills:
        named = ", ".join(f"`{qualify(s, plugin)}`" for s in skills)
        instructions += f"\n\n## Skills\n\nLoad these skills before starting: {named}."

    # Literal strings take no escapes, so the Markdown body survives verbatim --
    # basic strings would mangle every backslash in it.
    if "'''" in instructions:
        raise ValueError("body contains ''' and cannot be a TOML literal")

    lines = [
        f"name = {basic_string(name)}",
        f"description = {basic_string(scalar(fields, 'description'))}",
    ]
    mode = scalar(fields, "permissionMode") if "permissionMode" in fields else None
    sandbox = PERMISSION_MODE_TO_SANDBOX.get(mode) if mode else None
    if sandbox:
        lines.append(f'sandbox_mode = "{sandbox}"')
    lines.append(f"developer_instructions = '''\n{instructions}\n'''")
    return "\n".join(lines) + "\n"


def agent_targets(source: pathlib.Path, plugin: str) -> list[Target]:
    """Every agent role file for one plugin, as (path, contents) pairs."""
    targets: list[Target] = []
    for agent in sorted((source / "agents").glob("*.md")):
        fields, body = parse_frontmatter(agent.read_text(), agent)
        try:
            contents = render_agent_toml(fields, body, plugin)
        except ValueError as error:
            raise ValueError(f"{agent}: {error}") from None
        targets.append((source / "codex" / "agents" / f"{agent.stem}.toml", contents))
    return targets


def plugin_manifest(entry: Json) -> tuple[pathlib.Path, Json]:
    """Build a Codex plugin manifest from the Claude Code one.

    `skills` and `hooks` are omitted deliberately: Codex defaults them to
    `./skills` and `./hooks/hooks.json`, which is already our layout, and a
    redundant path is one more thing to drift.
    """
    source = ROOT / entry["source"].lstrip("./")
    claude = json.loads((source / ".claude-plugin" / "plugin.json").read_text())

    # The catalog and the manifest name the plugin independently; a one-sided
    # rename would leave the generated pair quietly disagreeing.
    if claude["name"] != entry["name"]:
        raise ValueError(
            f"{source}: plugin.json name {claude['name']!r} does not match "
            f"marketplace entry {entry['name']!r}"
        )

    manifest: Json = {
        "name": claude["name"],
        "version": claude["version"],
        "description": claude["description"],
        "interface": {
            "displayName": display_name(claude["name"]),
            "shortDescription": short_description(claude["description"]),
        },
    }
    if entry.get("keywords"):
        manifest["keywords"] = entry["keywords"]
    # Required, matching marketplace_manifest -- a category-less entry should
    # fail here rather than half-work in one manifest and raise in the other.
    manifest["interface"]["category"] = display_name(entry["category"])
    return source / ".codex-plugin" / "plugin.json", manifest


def marketplace_manifest(marketplace: Json) -> Json:
    """Build the Codex marketplace catalog.

    `policy` is omitted: Codex defaults installation to AVAILABLE and
    authentication to ON_INSTALL, which is what we want for every plugin.
    """
    return {
        "name": marketplace["name"],
        "interface": {"displayName": display_name(marketplace["name"])},
        "plugins": [
            {
                "name": entry["name"],
                "source": {"source": "local", "path": entry["source"]},
                "category": display_name(entry["category"]),
            }
            for entry in marketplace["plugins"]
        ],
    }


def as_json(manifest: Json) -> str:
    """Serialize a manifest the way the generated files are committed."""
    return json.dumps(manifest, indent=2) + "\n"


def collect_targets(marketplace: Json) -> list[Target]:
    """Every generated file, as (path, contents) pairs."""
    targets: list[Target] = [(CODEX_MARKETPLACE, as_json(marketplace_manifest(marketplace)))]

    for entry in marketplace["plugins"]:
        path, manifest = plugin_manifest(entry)
        targets.append((path, as_json(manifest)))

        source = ROOT / entry["source"].lstrip("./")
        if (source / "agents").is_dir():
            targets.extend(agent_targets(source, entry["name"]))

    return targets


def find_divergent_copies() -> list[pathlib.Path]:
    """Hook scripts that several plugins each ship a copy of.

    Plugins install independently, so they cannot share a module at hook runtime
    and the file has to be duplicated. Nothing else stops the copies drifting
    after a one-sided edit, so assert they are byte-identical here.
    """
    divergent: list[pathlib.Path] = []
    for relative in DUPLICATED_HOOK_SCRIPTS:
        copies = sorted(ROOT.glob(f"plugins/*/{relative}"))
        if len({copy.read_bytes() for copy in copies}) > 1:
            divergent.extend(copy.relative_to(ROOT) for copy in copies)
    return divergent


def find_orphans(targets: list[Target]) -> list[pathlib.Path]:
    """Generated files no longer produced by the generator.

    The forward pass only checks that each expected file is current, so a role
    left behind by a deleted agent stays invisible to it. That matters more than
    ordinary drift here: sync-codex-agents.js ships every `.toml` it finds, so an
    orphan would install into every Codex user's config with the check green.

    Every directory written to is owned wholly by this script, so anything in one
    that is not a target is an orphan. The directories to scan come from disk
    rather than from the targets: a plugin that drops to zero agents, or leaves
    the marketplace entirely, contributes no targets and would otherwise take its
    whole directory out of the scan along with the files left in it.
    """
    expected = {path for path, _ in targets}
    directories = (
        {path.parent for path in expected}
        | set(ROOT.glob("plugins/*/codex/agents"))
        | set(ROOT.glob("plugins/*/.codex-plugin"))
        | {CODEX_MARKETPLACE.parent}
    )
    return sorted(
        found.relative_to(ROOT)
        for directory in directories
        if directory.is_dir()
        for found in directory.glob("*")
        if found.is_file() and found not in expected
    )


def main() -> int:
    """Write the generated files, or with `--check` report any that are stale."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the generated files are current instead of writing them",
    )
    args = parser.parse_args()

    targets = collect_targets(json.loads(MARKETPLACE.read_text()))

    stale: list[pathlib.Path] = []
    for path, contents in targets:
        if args.check:
            current = path.read_text() if path.is_file() else None
            if current != contents:
                stale.append(path.relative_to(ROOT))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        print(f"wrote {path.relative_to(ROOT)}")

    orphans = find_orphans(targets) if args.check else []
    divergent = find_divergent_copies() if args.check else []

    if stale or orphans or divergent:
        if stale:
            print("stale Codex files -- run scripts/generate-codex.py:")
            for path in stale:
                print(f"  {path}")
        if orphans:
            print("orphaned Codex files -- delete them:")
            for path in orphans:
                print(f"  {path}")
        if divergent:
            print("duplicated hook scripts have diverged -- make them identical:")
            for path in divergent:
                print(f"  {path}")
        return 1
    if args.check:
        print(f"{len(targets)} Codex files current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
