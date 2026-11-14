from jobs.runner import run_jobs


def boom():
    raise RuntimeError("disk full")


def test_carries_on_past_a_failure():
    ran = []
    assert run_jobs({"a": boom, "b": lambda: ran.append("b")}) == ["a"]
    assert ran == ["b"]
