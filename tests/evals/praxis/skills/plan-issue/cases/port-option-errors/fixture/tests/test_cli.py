from devserve.cli import parse


def test_dir_defaults_to_here():
    assert parse([]).dir == "."
