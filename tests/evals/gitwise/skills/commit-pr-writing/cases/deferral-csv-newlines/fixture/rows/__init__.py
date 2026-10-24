"""Split CSV rows."""


def split_row(line: str) -> list[str]:
    """The fields of one CSV line."""
    return [field.strip('"') for field in line.split(",")]
