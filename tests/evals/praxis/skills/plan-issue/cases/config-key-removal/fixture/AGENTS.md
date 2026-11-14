# gatekeep

A self-hosted access proxy. Customers run it from our releases and keep their own
`config.toml`, which upgrades must keep reading.

- Python 3.12, standard library only.
- Run the tests with `python3 -m pytest -q`.
- Changes to `config.toml`'s keys are part of the public interface: ask before removing one.
