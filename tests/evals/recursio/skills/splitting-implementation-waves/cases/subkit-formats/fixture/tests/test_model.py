from subkit import Cue, ParseResult


def test_cue_defaults():
    c = Cue(1000, 2500, "Hello")
    assert c.speaker is None
    assert c.top is False


def test_parse_result_starts_empty():
    r = ParseResult()
    assert r.cues == [] and r.skipped == [] and r.title is None
