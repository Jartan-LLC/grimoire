from trip.planner import make_plan


def test_make_plan():
    assert make_plan([" a ", ""]) == ["a"]
