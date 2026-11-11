"""Merge contacts that are the same person."""


def key(contact: dict[str, str]) -> str:
    """What makes two contacts the same: their email, ignoring case and spaces."""
    return contact["email"].strip().lower()


def dedupe(contacts: list[dict[str, str]]) -> list[dict[str, str]]:
    """The contacts with later duplicates dropped, first seen kept, order kept."""
    kept: list[dict[str, str]] = []
    for contact in contacts:
        if all(key(contact) != key(other) for other in kept):
            kept.append(contact)
    return kept
