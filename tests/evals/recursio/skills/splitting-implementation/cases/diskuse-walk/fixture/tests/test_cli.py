from diskuse.cli import main


def test_main_runs():
    assert main([]) in (0, 1)
