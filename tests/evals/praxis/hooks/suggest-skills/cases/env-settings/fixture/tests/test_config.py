from mailer.config import load


def test_the_defaults():
    settings = load()
    assert (settings.smtp_host, settings.smtp_port) == ("smtp.internal", 587)
