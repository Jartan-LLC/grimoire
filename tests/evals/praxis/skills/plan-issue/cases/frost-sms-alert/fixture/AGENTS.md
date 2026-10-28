# greenhouse

Logs the greenhouse temperature from the sensor on the Raspberry Pi.

- Python 3.11, standard library only (the Pi has no pip).
- Tests: `python3 -m pytest -q`.
- Cron runs `python3 -m greenhouse` every ten minutes.
