import os
import pathlib

import pytest
from evals import cache, session
from evals.proc import GIT, run


def test_root_is_the_clones_git_common_dir_from_any_worktree_unless_overridden(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(cache.STORE, raising=False)
    env = session.git_env(dict(os.environ))
    clone, worktree = tmp_path / "clone", tmp_path / "worktree"
    run([GIT, "init", "-q", "-b", "main", str(clone)], env=env, check=True)
    run([GIT, "commit", "-q", "--allow-empty", "-m", "start"], cwd=clone, env=env, check=True)
    run([GIT, "worktree", "add", "-q", str(worktree)], cwd=clone, env=env, check=True)
    store = clone.resolve() / ".git" / "grimoire-evals"
    assert cache.root(clone) == store
    assert cache.root(worktree) == store
    monkeypatch.setenv(cache.STORE, str(tmp_path / "elsewhere"))
    assert cache.root(worktree) == tmp_path.resolve() / "elsewhere"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(cache.STORE, "relative/../store")
    assert cache.root(worktree) == tmp_path.resolve() / "store"
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv(cache.STORE, "~/store")
    assert cache.root(worktree) == tmp_path.resolve() / "home" / "store"


def test_cache_key_changes_with_every_input() -> None:
    base = cache.key("case", "arm", "model", "2.1.309", 0)
    for changed in (
        cache.key("case2", "arm", "model", "2.1.309", 0),
        cache.key("case", "arm2", "model", "2.1.309", 0),
        cache.key("case", "arm", "model2", "2.1.309", 0),
        cache.key("case", "arm", "model", "2.1.310", 0),
        cache.key("case", "arm", "model", "2.1.309", 1),
    ):
        assert changed != base
    assert cache.key("case", "arm", "model", "2.1.309", 0) == base


def test_cache_round_trips_a_sample_and_its_trace(tmp_path: pathlib.Path) -> None:
    sample = cache.Sample(
        "k1", "c1", "old", 0, {"demo": "/d"}, True, [], ["m"], "end", {}, {"cost_usd": 0.1}
    )
    cache.save(tmp_path, sample, '{"type": "result"}\n')
    assert cache.load(tmp_path, "k1") == sample
    assert cache.read_events(tmp_path, "k1") == '{"type": "result"}\n'
    assert cache.load(tmp_path, "k2") is None
