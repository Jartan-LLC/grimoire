"""Build the plugin sets a suite runs against: `old` from a git ref, `new` from the working tree."""

import io
import pathlib
import shutil
import tarfile
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass

from .proc import GIT, run
from .suite import tree_hash

# Names the cached `none` arm: bump it when what none_arm removes changes, so it is rebuilt.
NONE_REVISION = 2


@dataclass(frozen=True)
class Arm:
    """One plugin set: `plugins` maps each plugin's name to its directory."""

    name: str
    hash: str
    plugins: dict[str, str]

    @property
    def root(self) -> str:
        """The directory holding the arm's `plugins/`; empty for an arm with no plugin."""
        return next((str(pathlib.Path(d).parent.parent) for d in self.plugins.values()), "")


def _git(root: pathlib.Path, *args: str) -> bytes:
    return run([GIT, *args], cwd=root, capture_output=True, check=True).stdout


def arm_of(name: str, directory: pathlib.Path) -> Arm:
    """The arm whose plugins are `directory/plugins/*`, hashed over every file there.

    Every plugin goes in, as in a real install: one plugin's hooks and dependencies
    can shape another's behaviour.
    """
    plugins_dir = directory / "plugins"
    files = [p for p in plugins_dir.rglob("*") if p.is_file()]
    plugins = {
        p.parent.parent.name: str(p.parent.parent)
        for p in sorted(plugins_dir.glob("*/.claude-plugin/plugin.json"))
    }
    if not plugins:
        raise ValueError(f"{plugins_dir}: no plugin found")
    return Arm(name, tree_hash(plugins_dir, files), plugins)


def _install(staged: pathlib.Path, target: pathlib.Path) -> None:
    """Move a fully built arm into place; a concurrent build of the same arm may win the race."""
    try:
        staged.rename(target)
    except OSError:
        shutil.rmtree(staged, ignore_errors=True)


def old_arm(root: pathlib.Path, ref: str, store: pathlib.Path, name: str = "old") -> Arm:
    """`plugins/` as committed at `ref`, extracted once per tree under `store`.

    `name` lets an A/A comparison build a second arm from the same ref: the arm's
    name keeps its samples apart from the first's.
    """
    tree = _git(root, "rev-parse", f"{ref}:plugins").decode().strip()
    target = store / f"old-{tree}"
    if not target.is_dir():
        store.mkdir(parents=True, exist_ok=True)
        staged = pathlib.Path(tempfile.mkdtemp(dir=store, prefix=".build-"))
        archive = _git(root, "archive", "--format=tar", ref, "plugins/")
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(staged, filter="data")
        _install(staged, target)
    return arm_of(name, target)


def new_arm(root: pathlib.Path, store: pathlib.Path) -> Arm:
    """`plugins/` as in the working tree, tracked and untracked files not ignored."""
    listed = _git(root, "ls-files", "-z", "-co", "--exclude-standard", "plugins/").decode()
    files = [root / name for name in listed.split("\0") if name and (root / name).is_file()]
    target = store / f"new-{tree_hash(root, files)}"
    if not target.is_dir():
        store.mkdir(parents=True, exist_ok=True)
        staged = pathlib.Path(tempfile.mkdtemp(dir=store, prefix=".build-"))
        for path in files:
            copy = staged / path.relative_to(root)
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, copy)
        _install(staged, target)
    return arm_of("new", target)


def merge_base(root: pathlib.Path, base: str) -> str:
    """The commit `old` is taken from: where the branch left `base`, so other merges stay out."""
    return _git(root, "merge-base", base, "HEAD").decode().strip()


def _drop_preloads(agent: pathlib.Path, names: set[str]) -> None:
    lines = agent.read_text().split("\n")
    end = lines.index("---", 1) if lines and lines[0] == "---" and "---" in lines[1:] else 0
    kept = [
        line
        for i, line in enumerate(lines)
        if not (
            0 < i < end
            and (
                (line.strip().startswith("- ") and line.strip()[2:].strip() in names)
                or (line.startswith("skills:") and line[len("skills:") :].strip() in names)
            )
        )
    ]
    agent.write_text("\n".join(kept))


def _cut_body(document: pathlib.Path) -> None:
    lines = document.read_text().split("\n")
    end = lines.index("---", 1)
    body = [line for line in lines[end + 1 :] if line.strip()]
    document.write_text("\n".join([*lines[: end + 1], "", *body[:1], ""]))


def _holds(arm: Arm, target: str) -> bool:
    plugin, _, name = target.partition(":")
    return plugin in arm.plugins and any(
        (pathlib.Path(arm.plugins[plugin]) / part).exists()
        for part in (f"skills/{name}", f"agents/{name}.md", f"commands/{name}.md")
    )


def _remove(plugins: pathlib.Path, target: str) -> None:
    """Remove `target` from the plugin tree `plugins`, as `none_arm` says."""
    plugin, _, name = target.partition(":")
    root = plugins / plugin
    if (root / "skills" / name).is_dir():
        shutil.rmtree(root / "skills" / name)
        for agent in plugins.glob("*/agents/*.md"):
            names = {f"{plugin}:{name}"} | (
                {name} if agent.parent.parent.name == plugin else set[str]()
            )
            _drop_preloads(agent, names)
    elif (root / "agents" / f"{name}.md").is_file():
        _cut_body(root / "agents" / f"{name}.md")
    else:
        _cut_body(root / "commands" / f"{name}.md")


def none_arm(old: Arm, target: str, store: pathlib.Path, replaces: Sequence[str] = ()) -> Arm:
    """`old` with the text under test removed: `target`, and each text the target `replaces`.

    A skill's directory is deleted and every agent's preload of it dropped, so the
    agent starts without it; an agent's or command's body is cut to its first line,
    keeping its frontmatter so callers still find it. Pointers to a deleted skill in
    other files stay: an agent told to load it finds nothing, as with no skill at all.
    A text `old` does not hold, such as a new target, is left out; when `old` holds none
    of them, `none` is `old` as it is.
    """
    held = [t for t in (target, *replaces) if _holds(old, t)]
    if not held:
        return Arm("none", old.hash, old.plugins)
    source = pathlib.Path(next(iter(old.plugins.values()))).parent.parent
    removed = "+".join(t.replace(":", "-") for t in held)
    target_dir = store / f"none-r{NONE_REVISION}-{old.hash[:16]}-{removed}"
    if target_dir.is_dir():
        return arm_of("none", target_dir)
    store.mkdir(parents=True, exist_ok=True)
    staged = pathlib.Path(tempfile.mkdtemp(dir=store, prefix=".build-"))
    shutil.copytree(source, staged, dirs_exist_ok=True)
    for removing in held:
        _remove(staged / "plugins", removing)
    _install(staged, target_dir)
    return arm_of("none", target_dir)
