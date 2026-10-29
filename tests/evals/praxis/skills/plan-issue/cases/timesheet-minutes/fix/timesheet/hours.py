"""Hours as people type them in the sheet."""


def parse_hours(text: str) -> float:
    """Hours from "H:MM" ("7:30") or a decimal ("7.5")."""
    text = text.strip()
    if ":" in text:
        hours, minutes = text.split(":")
        return int(hours) + int(minutes) / 60
    return float(text)
