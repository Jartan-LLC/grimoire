"""Contacts are plain dicts with the keys name, email and phone.

TODO: these dicts have outgrown themselves. A typo in a key ("emial") fails silently;
a dataclass would catch it. Every module reads contacts by key, so it touches them all.
"""

KEYS = ("name", "email", "phone")


def make_contact(name: str, email: str, phone: str = "") -> dict[str, str]:
    """A contact with every key present."""
    return {"name": name.strip(), "email": email.strip().lower(), "phone": phone.strip()}


def same_person(a: dict[str, str], b: dict[str, str]) -> bool:
    """Two contacts are the same person when their emails match."""
    return a["email"] == b["email"]
