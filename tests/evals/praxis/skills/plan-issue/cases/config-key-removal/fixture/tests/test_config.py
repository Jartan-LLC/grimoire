from gatekeep.config import load


def test_loads_the_example():
    assert load("config.example.toml")["listen"] == "0.0.0.0:8443"
