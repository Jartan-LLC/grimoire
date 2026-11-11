"""Where and how mailer sends mail."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Mailer's settings."""

    smtp_host: str
    smtp_port: int
    timeout_s: float
    debug: bool


def load() -> Settings:
    """The settings mailer runs with."""
    return Settings(smtp_host="smtp.internal", smtp_port=587, timeout_s=10.0, debug=False)
