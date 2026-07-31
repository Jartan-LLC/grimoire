#!/usr/bin/env python3
"""Generate Codex manifests from the Claude Code manifests.

Source of truth is `.claude-plugin/marketplace.json` and each plugin's
`.claude-plugin/plugin.json`. This writes the Codex equivalents:

    plugins/<name>/.codex-plugin/plugin.json
    .agents/plugins/marketplace.json

Codex already reads the `.claude-plugin/` paths as a compatibility fallback, so
these files are not what makes the marketplace work -- they make it first-class,
carry the `interface` block Codex renders, and survive that fallback going away.

Run after changing a plugin's name, version, description, keywords, or category.
`--check` exits non-zero if the generated files are stale, for use in CI.
"""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"


def display_name(name):
    """Codex renders this in the plugin browser; our names are single words."""
    return name[:1].upper() + name[1:]


def short_description(description):
    """Lead clause of our `<summary> -- <detail>` description convention."""
    return description.split(" -- ")[0].strip()


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


def render(manifest):
    return json.dumps(manifest, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the generated files are current instead of writing them",
    )
    args = parser.parse_args()

    marketplace = json.loads(MARKETPLACE.read_text())
    targets = [(CODEX_MARKETPLACE, marketplace_manifest(marketplace))]
    targets.extend(plugin_manifest(entry) for entry in marketplace["plugins"])

    stale = []
    for path, manifest in targets:
        content = render(manifest)
        if args.check:
            current = path.read_text() if path.is_file() else None
            if current != content:
                stale.append(path.relative_to(ROOT))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"wrote {path.relative_to(ROOT)}")

    if stale:
        print("stale Codex manifests -- run scripts/generate-codex-manifests.py:")
        for path in stale:
            print(f"  {path}")
        return 1
    if args.check:
        print(f"{len(targets)} Codex manifests current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
