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


def display_name(name):
    """Codex renders this in the plugin browser; our names are single words."""
    return name[:1].upper() + name[1:]


def short_description(description):
    """Lead clause of our `<summary> -- <detail>` description convention."""
    return description.split(" -- ")[0].strip()


def parse_frontmatter(text):
    """Split a Markdown document into its YAML frontmatter and body.

    Deliberately minimal: our agent frontmatter is single-line scalars plus a
    `skills:` list, so a YAML dependency would buy nothing.
    """
    lines = text.split("\n")
    end = lines.index("---", 1)
    fields, key = {}, None

    for line in lines[1:end]:
        item = re.match(r"\s+-\s+(.*)$", line)
        if item and key:
            fields[key].append(item.group(1).strip())
            continue
        match = re.match(r"([A-Za-z_-]+):\s*(.*)$", line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            fields[key] = value if value else []

    return fields, "\n".join(lines[end + 1:]).strip()


def qualify(skill, plugin):
    """Codex namespaces plugin skills as `plugin:skill`, same as Claude Code."""
    return skill if ":" in skill else f"{plugin}:{skill}"


def render_agent_toml(fields, body, plugin):
    """Render one Claude Code agent as a Codex agent role.

    `skills:` has no Codex equivalent, so the preloaded skills are named in the
    instructions instead. Dropping them silently would strip the reviewers of
    their severity model and conventions -- the grounding that makes findings
    land the same tier whoever raises them.
    """
    instructions = body
    if fields.get("skills"):
        named = ", ".join(f"`{qualify(s, plugin)}`" for s in fields["skills"])
        instructions += f"\n\n## Skills\n\nLoad these skills before starting: {named}."

    # Literal strings take no escapes, so the Markdown body survives verbatim --
    # basic strings would mangle every backslash in it.
    if "'''" in instructions:
        raise ValueError(f"{fields['name']}: body contains ''' and cannot be a TOML literal")

    lines = [f'name = "{fields["name"]}"', f'description = "{fields["description"]}"']
    sandbox = PERMISSION_MODE_TO_SANDBOX.get(fields.get("permissionMode"))
    if sandbox:
        lines.append(f'sandbox_mode = "{sandbox}"')
    lines.append(f"developer_instructions = '''\n{instructions}\n'''")
    return "\n".join(lines) + "\n"


def agent_targets(source, plugin):
    """Every agent role file for one plugin, as (path, contents) pairs."""
    return [
        (source / "codex" / "agents" / f"{agent.stem}.toml",
         render_agent_toml(*parse_frontmatter(agent.read_text()), plugin))
        for agent in sorted((source / "agents").glob("*.md"))
    ]


def plugin_manifest(entry):
    """Build a Codex plugin manifest from the Claude Code one.

    `skills` and `hooks` are omitted deliberately: Codex defaults them to
    `./skills` and `./hooks/hooks.json`, which is already our layout, and a
    redundant path is one more thing to drift.
    """
    source = ROOT / entry["source"].lstrip("./")
    claude = json.loads((source / ".claude-plugin" / "plugin.json").read_text())

    manifest = {
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
    if entry.get("category"):
        manifest["interface"]["category"] = display_name(entry["category"])
    return source / ".codex-plugin" / "plugin.json", manifest


def marketplace_manifest(marketplace):
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


def as_json(manifest):
    return json.dumps(manifest, indent=2) + "\n"


def collect_targets(marketplace):
    """Every generated file, as (path, contents) pairs."""
    targets = [(CODEX_MARKETPLACE, as_json(marketplace_manifest(marketplace)))]

    for entry in marketplace["plugins"]:
        path, manifest = plugin_manifest(entry)
        targets.append((path, as_json(manifest)))

        source = ROOT / entry["source"].lstrip("./")
        if (source / "agents").is_dir():
            targets.extend(agent_targets(source, entry["name"]))

    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the generated files are current instead of writing them",
    )
    args = parser.parse_args()

    targets = collect_targets(json.loads(MARKETPLACE.read_text()))

    stale = []
    for path, contents in targets:
        if args.check:
            current = path.read_text() if path.is_file() else None
            if current != contents:
                stale.append(path.relative_to(ROOT))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        print(f"wrote {path.relative_to(ROOT)}")

    if stale:
        print("stale Codex files -- run scripts/generate-codex.py:")
        for path in stale:
            print(f"  {path}")
        return 1
    if args.check:
        print(f"{len(targets)} Codex files current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
