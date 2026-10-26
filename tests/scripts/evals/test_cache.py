import pathlib

from evals import cache


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
