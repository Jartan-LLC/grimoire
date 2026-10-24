#!/usr/bin/env python3
"""Check that every skill, agent and command a plugin points to exists, and is declared.

An agent's `skills:` entry is a hard load: one naming no skill fails the agent once
released. A `<plugin>:<name>` in a skill, agent, command or hook tells the agent to
load that skill, or names that agent or command; one naming nothing points nowhere,
and nothing at runtime says so. Such a pointer into another plugin, or a bare mention
of another plugin's name, needs that plugin in the manifest's `dependencies`
(GUARDRAILS.md): an undeclared plugin may not be installed. Each file's frontmatter
`name` must also match its directory or file name, and its `description` be present.

Unqualified names in prose ("spawn `backend-reviewer`") are not checked: telling a
load from an example would be guesswork.
"""

import importlib.util
import json
import pathlib
import re
import sys
from collections.abc import Callable, Iterable
from typing import cast

ROOT = pathlib.Path(__file__).resolve().parent.parent

type Frontmatter = dict[str, str | list[str]]


def _parse_frontmatter() -> Callable[[str, pathlib.Path], tuple[Frontmatter, str]]:
    """generate-codex.py's parser, so both scripts read frontmatter alike.

    Loaded by path: its hyphenated file name can't be imported by name.
    """
    path = pathlib.Path(__file__).resolve().parent / "generate-codex.py"
    spec = importlib.util.spec_from_file_location("generate_codex", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast("Callable[[str, pathlib.Path], tuple[Frontmatter, str]]", module.parse_frontmatter)


parse_frontmatter = _parse_frontmatter()


def declared(manifest: dict[str, object]) -> set[str]:
    """The plugin names a manifest's `dependencies` lists, whatever their marketplace."""
    deps = manifest.get("dependencies", [])
    names: set[str] = set()
    for dep in cast("list[object]", deps) if isinstance(deps, list) else []:
        if isinstance(dep, str):
            names.add(dep.partition("@")[0])
        elif isinstance(dep, dict):
            name = cast("dict[str, object]", dep).get("name")
            if isinstance(name, str):
                names.add(name)
    return names


def manifests() -> dict[str, dict[str, object]]:
    """Each plugin's name, with its parsed plugin.json."""
    return {
        manifest.parent.parent.name: json.loads(manifest.read_text())
        for manifest in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
    }


def documents(plugin: str) -> list[pathlib.Path]:
    """The plugin's skill, agent and command files, the ones with frontmatter."""
    return [
        *sorted(ROOT.glob(f"plugins/{plugin}/skills/*/SKILL.md")),
        *sorted(ROOT.glob(f"plugins/{plugin}/agents/*.md")),
        *sorted(ROOT.glob(f"plugins/{plugin}/commands/*.md")),
    ]


def qualified_pattern(plugins: Iterable[str]) -> re.Pattern[str]:
    """A `<plugin>:<name>` reference to one of `plugins`, capturing both parts."""
    names = "|".join(re.escape(p) for p in plugins)
    return re.compile(rf"\b({names}):([a-z0-9][a-z0-9-]*)")


def references() -> dict[pathlib.Path, set[tuple[str, str]]]:
    """Each skill, agent, command and hook file, with the (plugin, name) pairs it points to.

    The pointers problems() checks: `skills:` entries, an unqualified one naming the
    file's own plugin, and every `<plugin>:<name>` in its frontmatter, body or hook
    text. A file that does not parse is left out; problems() reports it.
    """
    plugins = manifests()
    qualified = qualified_pattern(plugins)
    found: dict[pathlib.Path, set[tuple[str, str]]] = {}
    for own in plugins:
        for path in documents(own):
            try:
                fields, body = parse_frontmatter(path.read_text(), path.relative_to(ROOT))
            except ValueError:
                continue
            entries = fields.get("skills", [])
            pairs = {
                (plugin or own, name)
                for plugin, _, name in (
                    e.rpartition(":") for e in ([entries] if isinstance(entries, str) else entries)
                )
            }
            values = [v for k, v in fields.items() if k != "skills" and isinstance(v, str)]
            text = "\n".join([*values, body])
            pairs |= {(m.group(1), m.group(2)) for m in qualified.finditer(text)}
            found[path] = pairs
        for path in sorted(ROOT.glob(f"plugins/{own}/hooks/*.json")):
            found[path] = {(m.group(1), m.group(2)) for m in qualified.finditer(path.read_text())}
    return found


def problems() -> list[str]:
    """One message per broken or undeclared pointer, mismatched name or missing description."""
    plugins = manifests()
    if not plugins:
        return ["no plugins/*/.claude-plugin/plugin.json found -- nothing was checked"]
    skills = {
        (p, s.parent.name) for p in plugins for s in ROOT.glob(f"plugins/{p}/skills/*/SKILL.md")
    }
    others = {
        (p, f.stem)
        for p in plugins
        for kind in ("agents", "commands")
        for f in ROOT.glob(f"plugins/{p}/{kind}/*.md")
    }
    names = "|".join(re.escape(p) for p in plugins)
    qualified = qualified_pattern(plugins)
    bare = re.compile(rf"\b({names})\b(?!:[a-z0-9])")
    found: list[str] = []

    def pointer(
        where: str, own: str, plugin: str, name: str, targets: set[tuple[str, str]]
    ) -> None:
        deps = declared(plugins[own])
        if plugin != own and plugin not in deps:
            found.append(f"{where}: {plugin}:{name} is in {plugin}, which {own} does not declare")
        elif plugin in plugins and (plugin, name) not in targets:
            kinds = "skill" if targets is skills else "skill, agent or command"
            found.append(f"{where}: {plugin}:{name} names no {kinds}")

    def pointers(where: str, own: str, text: str, targets: set[tuple[str, str]]) -> None:
        deps = declared(plugins[own])
        for match in qualified.finditer(text):
            pointer(where, own, match.group(1), match.group(2), targets)
        found.extend(
            f"{where}: names {match.group()}, which {own} does not declare"
            for match in bare.finditer(text)
            if match.group() != own and match.group() not in deps
        )

    for own in plugins:
        for path in documents(own):
            where = path.relative_to(ROOT)
            try:
                fields, body = parse_frontmatter(path.read_text(), where)
            except ValueError as error:
                found.append(str(error))
                continue
            expected = path.parent.name if path.name == "SKILL.md" else path.stem
            if fields.get("name") != expected:
                found.append(f"{where}: name {fields.get('name')!r} differs from {expected!r}")
            if not isinstance(fields.get("description"), str):
                found.append(f"{where}: no description")
            entries = fields.get("skills", [])
            for entry in [entries] if isinstance(entries, str) else entries:
                plugin, _, name = entry.rpartition(":")
                pointer(str(where), own, plugin or own, name, skills)
            values = [v for k, v in fields.items() if k != "skills" and isinstance(v, str)]
            pointers(str(where), own, "\n".join([*values, body]), skills | others)
        for path in sorted(ROOT.glob(f"plugins/{own}/hooks/*.json")):
            pointers(str(path.relative_to(ROOT)), own, path.read_text(), skills)
    return list(dict.fromkeys(found))


def main() -> int:
    """Report every problem found; exit 1 if there is any."""
    found = problems()
    for message in found:
        print(message)
    if found:
        return 1
    print("every skill, agent and command pointer resolves, within declared dependencies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
