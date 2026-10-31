# SPDX-License-Identifier: 0BSD
"""ISBN-10 and ISBN-13 check digits."""


def clean(isbn: str) -> str:
    """The ISBN without hyphens or spaces, with a final x as X."""
    return isbn.replace("-", "").replace(" ", "").upper()


def is_valid10(digits: str) -> bool:
    """Whether a cleaned ISBN-10 has the right check digit."""
    if len(digits) != 10 or not digits[:9].isdigit() or not (digits[9].isdigit() or digits[9] == "X"):
        return False
    values = [int(d) for d in digits[:9]] + [10 if digits[9] == "X" else int(digits[9])]
    return sum((10 - i) * v for i, v in enumerate(values)) % 11 == 0


def is_valid13(digits: str) -> bool:
    """Whether a cleaned ISBN-13 has the right check digit."""
    if len(digits) != 13 or not digits.isdigit():
        return False
    return sum((3 if i % 2 else 1) * int(d) for i, d in enumerate(digits)) % 10 == 0


def is_valid(isbn: str) -> bool:
    """Whether the ISBN, of either length, is valid."""
    digits = clean(isbn)
    return is_valid10(digits) or is_valid13(digits)


def to13(digits: str) -> str:
    """A valid cleaned ISBN as its ISBN-13."""
    if len(digits) == 13:
        return digits
    body = "978" + digits[:9]
    check = (10 - sum((3 if i % 2 else 1) * int(d) for i, d in enumerate(body)) % 10) % 10
    return body + str(check)
