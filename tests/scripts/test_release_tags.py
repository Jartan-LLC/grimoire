import json
import os
import pathlib
import subprocess

import pytest
from script_loader import load_script

rt = load_script("release-tags.py")


def m(name: str, version: str, *deps: str) -> object:
    return rt.Manifest(name=name, version=version, dependencies=frozenset(deps))


def test_parse_manifest_reads_string_and_object_dependencies() -> None:
    text = (
        '{"name": "p", "version": "1.7.0", "dependencies": ["a", {"name": "b", "version": "^1"}]}'
    )
    assert rt.parse_manifest(text) == m("p", "1.7.0", "a", "b")


def test_parse_manifest_without_dependencies() -> None:
    assert rt.parse_manifest('{"name": "p", "version": "2.0.0-rc1"}') == m("p", "2.0.0-rc1")


def test_only_changed_versions_are_tagged() -> None:
    head = {"gitwise": m("gitwise", "1.2.0"), "praxis": m("praxis", "1.7.0", "gitwise")}
    base = {"gitwise": m("gitwise", "1.2.0"), "praxis": m("praxis", "1.6.0", "gitwise")}
    assert rt.due_tags(base=base, head=head) == ["praxis--v1.7.0"]


def test_no_version_change_tags_nothing() -> None:
    same = {"gitwise": m("gitwise", "1.2.0")}
    assert rt.due_tags(base=same, head=same) == []


def test_dependency_is_tagged_before_the_plugin_that_needs_it() -> None:
    # "praxis" sorts after "gitwise" either way, so use a name that sorts first.
    head = {"aaa": m("aaa", "2.0.0", "zzz"), "zzz": m("zzz", "1.1.0")}
    base = {"aaa": m("aaa", "1.0.0", "zzz"), "zzz": m("zzz", "1.0.0")}
    assert rt.due_tags(base=base, head=head) == ["zzz--v1.1.0", "aaa--v2.0.0"]


def test_unrelated_plugins_come_out_by_name() -> None:
    head = {"b": m("b", "1.1.0"), "a": m("a", "1.1.0")}
    base = {"b": m("b", "1.0.0"), "a": m("a", "1.0.0")}
    assert rt.due_tags(base=base, head=head) == ["a--v1.1.0", "b--v1.1.0"]


def test_a_plugin_new_at_head_is_tagged() -> None:
    assert rt.due_tags(base={}, head={"new": m("new", "0.1.0")}) == ["new--v0.1.0"]


def test_a_removed_plugin_tags_nothing() -> None:
    assert rt.due_tags(base={"old": m("old", "1.0.0")}, head={}) == []


def test_a_dependency_cycle_raises_instead_of_dropping_tags() -> None:
    head = {"a": m("a", "1.1.0", "b"), "b": m("b", "1.1.0", "a")}
    base = {"a": m("a", "1.0.0", "b"), "b": m("b", "1.0.0", "a")}
    with pytest.raises(ValueError, match="cycle"):
        rt.due_tags(base=base, head=head)


def git(repo: pathlib.Path, *args: str) -> str:
    # Fixed git argv in a temporary fixture repository, never this checkout.
    return subprocess.run(  # noqa: S603
        [rt.GIT, "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def commit_plugins(repo: pathlib.Path, plugins: dict[str, str], message: str) -> str:
    for name, version in plugins.items():
        manifest = repo / "plugins" / name / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"name": name, "version": version}))
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)
    return git(repo, "rev-parse", "HEAD")


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
    git(tmp_path, "init", "-q")
    (tmp_path / "README.md").write_text("x\n")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "commit", "-qm", "root")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_manifests_at_reads_every_plugin_at_a_commit(repo: pathlib.Path) -> None:
    # A directory under plugins/ without a plugin.json is not a plugin.
    (repo / "plugins" / "notes").mkdir(parents=True)
    (repo / "plugins" / "notes" / "README.md").write_text("x\n")
    sha = commit_plugins(repo, {"a": "1.0.0", "b": "2.0.0"}, "two plugins")
    assert "notes" in git(repo, "ls-tree", "-d", "--name-only", f"{sha}:plugins").split()
    assert rt.manifests_at(sha) == {"a": m("a", "1.0.0"), "b": m("b", "2.0.0")}


def test_manifests_at_a_commit_without_plugins_is_empty(repo: pathlib.Path) -> None:
    assert rt.manifests_at("HEAD") == {}


def test_manifests_at_a_ref_that_names_no_commit_raises(repo: pathlib.Path) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        rt.manifests_at("no-such-ref")


def test_untagged_lists_current_versions_without_a_known_tag_by_name() -> None:
    plugins = {"b": m("b", "2.0.0"), "a": m("a", "1.0.0"), "c": m("c", "3.0.0")}
    assert rt.untagged(plugins, {"c--v3.0.0", "a--v0.9.0"}) == ["a--v1.0.0", "b--v2.0.0"]


def test_untagged_is_empty_when_every_version_is_known() -> None:
    assert rt.untagged({"a": m("a", "1.0.0")}, {"a--v1.0.0"}) == []


def test_manifests_at_rejects_a_directory_named_unlike_its_manifest(repo: pathlib.Path) -> None:
    manifest = repo / "plugins" / "dir" / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": "other", "version": "1.0.0"}))
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "mismatch")
    with pytest.raises(ValueError, match="declares name 'other'"):
        rt.manifests_at("HEAD")


def test_cli_due_and_untagged_as_the_workflow_calls_them(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    first = commit_plugins(repo, {"a": "1.0.0", "b": "1.0.0"}, "first")
    commit_plugins(repo, {"a": "1.1.0"}, "bump a")
    (repo / "README.md").write_text("y\n")
    git(repo, "commit", "-qam", "no bump")
    monkeypatch.setattr("sys.argv", ["release-tags.py", "due", first, "HEAD"])
    assert rt.main() == 0
    assert capsys.readouterr().out.split() == ["a--v1.1.0"]
    known = repo / "known.txt"
    known.write_text("a--v1.1.0\n")
    monkeypatch.setattr("sys.argv", ["release-tags.py", "untagged", "HEAD", str(known)])
    assert rt.main() == 0
    assert capsys.readouterr().out.split() == ["b--v1.0.0"]


def test_parse_manifest_leaves_out_another_marketplaces_dependency() -> None:
    text = (
        '{"name": "p", "version": "1.0.0", "dependencies": '
        '[{"name": "gitwise", "version": "^1", "marketplace": "other"}, "local"]}'
    )
    assert rt.parse_manifest(text) == m("p", "1.0.0", "local")


def test_parse_manifest_keeps_a_dependency_named_in_its_own_marketplace() -> None:
    text = (
        '{"name": "p", "version": "1.0.0", "dependencies": ['
        '{"name": "gitwise", "version": "^1", "marketplace": "grimoire"}, '
        '"tools@grimoire", "far@other"]}'
    )
    assert rt.parse_manifest(text, "grimoire") == m("p", "1.0.0", "gitwise", "tools")
