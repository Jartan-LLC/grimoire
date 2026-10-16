import pytest
from script_loader import load_script

rt = load_script("release-tags.py")


def m(version: str, *deps: str) -> object:
    return rt.Manifest(version=version, dependencies=frozenset(deps))


def test_parse_manifest_reads_string_and_object_dependencies() -> None:
    text = (
        '{"name": "p", "version": "1.7.0", "dependencies": ["a", {"name": "b", "version": "^1"}]}'
    )
    assert rt.parse_manifest(text) == m("1.7.0", "a", "b")


def test_parse_manifest_without_dependencies() -> None:
    assert rt.parse_manifest('{"name": "p", "version": "2.0.0-rc1"}') == m("2.0.0-rc1")


def test_only_changed_versions_are_tagged() -> None:
    head = {"gitwise": m("1.2.0"), "praxis": m("1.7.0", "gitwise")}
    base = {"gitwise": m("1.2.0"), "praxis": m("1.6.0", "gitwise")}
    assert rt.due_tags(head, base) == ["praxis--v1.7.0"]


def test_no_version_change_tags_nothing() -> None:
    same = {"gitwise": m("1.2.0")}
    assert rt.due_tags(same, same) == []


def test_dependency_is_tagged_before_the_plugin_that_needs_it() -> None:
    # "praxis" sorts after "gitwise" either way, so use a name that sorts first.
    head = {"aaa": m("2.0.0", "zzz"), "zzz": m("1.1.0")}
    base = {"aaa": m("1.0.0", "zzz"), "zzz": m("1.0.0")}
    assert rt.due_tags(head, base) == ["zzz--v1.1.0", "aaa--v2.0.0"]


def test_unrelated_plugins_come_out_by_name() -> None:
    head = {"b": m("1.1.0"), "a": m("1.1.0")}
    base = {"b": m("1.0.0"), "a": m("1.0.0")}
    assert rt.due_tags(head, base) == ["a--v1.1.0", "b--v1.1.0"]


def test_a_plugin_new_at_head_is_tagged() -> None:
    assert rt.due_tags({"new": m("0.1.0")}, {}) == ["new--v0.1.0"]


def test_a_removed_plugin_tags_nothing() -> None:
    assert rt.due_tags({}, {"old": m("1.0.0")}) == []


def test_a_dependency_cycle_raises_instead_of_dropping_tags() -> None:
    head = {"a": m("1.1.0", "b"), "b": m("1.1.0", "a")}
    base = {"a": m("1.0.0", "b"), "b": m("1.0.0", "a")}
    with pytest.raises(ValueError, match="cycle"):
        rt.due_tags(head, base)
