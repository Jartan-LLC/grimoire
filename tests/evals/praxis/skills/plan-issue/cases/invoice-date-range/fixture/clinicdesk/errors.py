"""Errors the server turns into HTTP answers."""


class BadRequest(ValueError):
    """The request's query is invalid; the server answers 400 with the message."""
