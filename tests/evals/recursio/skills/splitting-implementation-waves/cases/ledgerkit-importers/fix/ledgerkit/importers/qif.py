"""QIF (Quicken Interchange Format) importer, as specified in docs/formats/qif.md."""

import re
from datetime import date
from decimal import Decimal

from ledgerkit.model import FormatError, ImportResult, Skipped, Transaction

_TYPES = ("Bank", "CCard", "Cash")
_DATE = re.compile(r"\s*(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*(?:[/.-]\s*(\d{4}|\d{2})|'\s*(\d{2}))\s*")
_AMOUNT = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)")

_Field = tuple[str, str]


def sniff(text: str) -> bool:
    """True when the first non-blank line starts with `!Type:`."""
    for line in text.split("\n"):
        if line.strip():
            return line.startswith("!Type:")
    return False


def parse(text: str) -> ImportResult:
    """Read every record; malformed ones become `Skipped`."""
    lines = text.split("\n")
    header_index = next((i for i, line in enumerate(lines) if line.strip()), None)
    if header_index is None or not lines[header_index].startswith("!Type:"):
        raise FormatError("not a QIF file")
    qif_type = lines[header_index].rstrip().removeprefix("!Type:")
    if qif_type not in _TYPES:
        raise FormatError(f"unsupported QIF type: {qif_type}")

    result = ImportResult()
    for start, fields in _records(lines[header_index + 1 :], header_index + 2):
        try:
            result.transactions.extend(_build(fields))
        except ValueError as error:
            result.skipped.append(Skipped(start, str(error)))
    return result


def dump(transactions: list[Transaction], type: str = "Bank") -> str:  # noqa: A002
    """Write the transactions as QIF records under a `!Type:<type>` header."""
    if type not in _TYPES:
        raise FormatError(f"unsupported QIF type: {type}")
    out = [f"!Type:{type}"]
    for t in transactions:
        for value in (t.payee, t.memo, t.ref or "", t.category or ""):
            if "\n" in value or "\r" in value:
                raise FormatError("line break in a QIF field")
        out.append(f"D{t.day.month:02}/{t.day.day:02}/{t.day.year:04}")
        out.append(f"T{t.amount:.2f}")
        out.append(f"P{t.payee}")
        if t.memo:
            out.append(f"M{t.memo}")
        if t.ref is not None:
            out.append(f"N{t.ref}")
        if t.category:
            out.append(f"L{_category_out(t.category)}")
        out.append("^")
    return "\n".join(out) + "\n"


def _records(lines: list[str], first_line: int) -> list[tuple[int, list[_Field]]]:
    """Group lines into records: (line of the first field, its (code, value) fields)."""
    records: list[tuple[int, list[_Field]]] = []
    start = first_line
    fields: list[_Field] = []
    for number, raw in enumerate(lines, first_line):
        line = raw.removesuffix("\r")
        if line == "^":
            if fields:
                records.append((start, fields))
            fields = []
        elif line.strip():
            if not fields:
                start = number
            fields.append((line[0], line[1:]))
    if fields:
        records.append((start, fields))
    return records


def _build(fields: list[_Field]) -> list[Transaction]:
    """Turn one record into its transactions; ValueError carries the skip reason."""
    values = {code: value for code, value in fields if code in "DTUPMNL"}
    if "D" not in values:
        raise ValueError("missing date")
    if "T" not in values and "U" not in values:
        raise ValueError("missing amount")
    day = _parse_date(values["D"])
    amount = _parse_amount(values["T"] if "T" in values else values["U"])
    common = {
        "day": day,
        "payee": values.get("P", ""),
        "ref": values.get("N") or None,
    }

    splits = _splits(fields)
    if not splits:
        category = _category_in(values.get("L", ""))
        return [Transaction(amount=amount, memo=values.get("M", ""), category=category, **common)]
    if sum((split["amount"] for split in splits), Decimal(0)) != amount:
        raise ValueError("splits do not add up")
    return [
        Transaction(
            amount=split["amount"],
            memo=split["memo"] if split["memo"] is not None else values.get("M", ""),
            category=_category_in(split["category"]),
            **common,
        )
        for split in splits
    ]


def _splits(fields: list[_Field]) -> list[dict]:
    """Collect the S/E/$ groups; each group starts at its S line."""
    groups: list[dict] = []
    for code, value in fields:
        if code == "S":
            groups.append({"category": value, "memo": None, "amount": None})
        elif groups and code == "E":
            groups[-1]["memo"] = value
        elif groups and code == "$":
            groups[-1]["amount"] = _parse_amount(value)
    if any(group["amount"] is None for group in groups):
        raise ValueError("split without amount")
    return groups


def _parse_date(value: str) -> date:
    match = _DATE.fullmatch(value)
    if not match:
        raise ValueError(f"bad date: {value.strip()!r}")
    month, day, long_year, short_year = match.groups()
    year = int(long_year) if long_year and len(long_year) == 4 else 2000 + int(long_year or short_year)
    try:
        return date(year, int(month), int(day))
    except ValueError:
        raise ValueError(f"bad date: {value.strip()!r}") from None


def _parse_amount(value: str) -> Decimal:
    cleaned = value.strip().replace(",", "")
    if not _AMOUNT.fullmatch(cleaned):
        raise ValueError(f"bad amount: {value.strip()!r}")
    return Decimal(cleaned)


def _category_in(value: str) -> str | None:
    """Map an L/S value to a category; brackets mean a transfer."""
    if value.startswith("[") and value.endswith("]"):
        return f"transfer:{value[1:-1]}"
    return value or None


def _category_out(category: str) -> str:
    return f"[{category.removeprefix('transfer:')}]" if category.startswith("transfer:") else category
