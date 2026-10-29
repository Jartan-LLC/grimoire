import pytest

from pingmon.config import ConfigError, parse


def test_fills_defaults():
    [check] = parse('[[check]]\nurl = "https://a"\n')
    assert check == {"url": "https://a", "interval_s": 60, "timeout_s": 10, "retries": 0}


def test_rejects_unknown_keys():
    with pytest.raises(ConfigError, match="unknown key 'timeout'"):
        parse('[[check]]\nurl = "https://a"\ntimeout = 5\n')
