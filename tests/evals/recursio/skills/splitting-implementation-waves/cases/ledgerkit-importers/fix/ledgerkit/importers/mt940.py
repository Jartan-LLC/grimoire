"""MT940 (SWIFT customer statement) importer: `sniff`, `parse` and `dump`."""

import re
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from ledgerkit.model import FormatError, ImportResult, Skipped, Transaction

_TAG = re.compile(r":(\d{2}[A-Z]?):(.*)")
_END_LINES = frozenset({"-", "-}"})
_LINE61 = re.compile(
    r"(?P<value>\d{6})(?:\d{4})?(?P<mark>RC|RD|C|D)(?:[A-Za-z])?(?P<amount>\d+,\d*)"
    r"[NF][A-Za-z0-9]{3}(?P<rest>.*)"
)
_BALANCE = re.compile(r"(?P<mark>[CD])\d{6}(?P<currency>[A-Z]{3})(?P<amount>\d+,\d*)")
_NEGATIVE_MARKS = frozenset({"D", "RC"})
_MAX_AMOUNT_CHARS = 15
_MAX_REF_CHARS = 16
_MAX_DETAIL_CHARS = 65
_DEFAULT_CURRENCY = "EUR"
_NO_REF = "NONREF"


@dataclass
class _Field:
    """A tagged field: its tag, the 1-based line it starts on and its text lines."""

    tag: str
    line: int
    lines: list[str]


def sniff(text: str) -> bool:
    """True when one of the first ten lines starts with `:20:`."""
    return any(line.startswith(":20:") for line in text.split("\n")[:10])


def parse(text: str) -> ImportResult:
    """Read every statement; a statement that fails its checks is skipped as a whole."""
    statements = _split_statements([line.rstrip("\r") for line in text.split("\n")])
    if not statements:
        raise FormatError("no :20: statement found")
    result = ImportResult()
    for fields in statements:
        statement = _read_statement(fields)
        result.transactions.extend(statement.transactions)
        result.skipped.extend(statement.skipped)
    return result


def dump(transactions: list[Transaction], account: str, opening: Decimal = Decimal("0")) -> str:
    """Write the transactions as one statement; they must share one currency."""
    if not transactions:
        return ""
    currency = transactions[0].currency
    if any(t.currency != currency for t in transactions):
        raise FormatError("transactions have more than one currency")
    closing = opening + sum((t.amount for t in transactions), Decimal(0))
    lines = [
        ":20:LEDGERKIT",
        f":25:{account}",
        ":28C:1/1",
        f":60F:{_format_balance(opening, transactions[0].day, currency)}",
    ]
    for t in transactions:
        lines.extend(_dump_transaction(t))
    lines.append(f":62F:{_format_balance(closing, transactions[-1].day, currency)}")
    lines.append("-")
    return "\n".join(lines) + "\n"


def _split_statements(lines: list[str]) -> list[list[_Field]]:
    """Group the tagged fields by statement; text outside statements is dropped."""
    statements: list[list[_Field]] = []
    current: list[_Field] | None = None
    field: _Field | None = None
    for number, line in enumerate(lines, 1):
        if line in _END_LINES:
            current = field = None
            continue
        match = _TAG.fullmatch(line)
        if match is None:
            if field is not None:
                field.lines.append(line)
            continue
        tag, first = match.groups()
        if tag == "20":
            current = []
            statements.append(current)
        if current is None:
            field = None
            continue
        field = _Field(tag, number, [first])
        current.append(field)
    return statements


def _read_statement(fields: list[_Field]) -> ImportResult:
    """Read one statement's transactions and apply the balance check."""
    opening = _find_balance(fields, ("60F", "60M"))
    closing = _find_balance(fields, ("62F", "62M"))
    currency = opening[1] if opening else _DEFAULT_CURRENCY
    result = ImportResult()
    awaiting_details = False
    for field in fields:
        if field.tag == "61":
            try:
                result.transactions.append(_parse_line61(field.lines[0], currency))
            except ValueError:
                result.skipped.append(Skipped(field.line, "malformed :61:"))
                awaiting_details = False
            else:
                awaiting_details = True
        elif field.tag == "86" and awaiting_details:
            payee, memo = _parse_details(field.lines)
            result.transactions[-1] = replace(result.transactions[-1], payee=payee, memo=memo)
            awaiting_details = False
    if result.skipped:
        return result
    start = fields[0].line
    if opening is None or closing is None:
        return ImportResult(skipped=[Skipped(start, "missing balance")])
    if opening[0] + sum((t.amount for t in result.transactions), Decimal(0)) != closing[0]:
        return ImportResult(skipped=[Skipped(start, "balance mismatch")])
    return result


def _find_balance(fields: list[_Field], tags: tuple[str, ...]) -> tuple[Decimal, str] | None:
    """The first balance field with one of the tags as (signed amount, currency)."""
    for field in fields:
        if field.tag in tags:
            match = _BALANCE.fullmatch("".join(field.lines).strip())
            if match is None:
                return None
            amount = _decimal(match["amount"])
            return (-amount if match["mark"] == "D" else amount), match["currency"]
    return None


def _parse_line61(text: str, currency: str) -> Transaction:
    """Read a `:61:` line; raise ValueError when it does not match the layout."""
    match = _LINE61.fullmatch(text)
    if match is None or len(match["amount"]) > _MAX_AMOUNT_CHARS:
        raise ValueError(text)
    ref = match["rest"].partition("//")[0]
    if not 1 <= len(ref) <= _MAX_REF_CHARS:
        raise ValueError(text)
    value = match["value"]
    day = date(2000 + int(value[:2]), int(value[2:4]), int(value[4:]))
    amount = _decimal(match["amount"])
    return Transaction(
        day=day,
        amount=-amount if match["mark"] in _NEGATIVE_MARKS else amount,
        payee="",
        ref=None if ref == _NO_REF else ref,
        currency=currency,
    )


def _parse_details(lines: list[str]) -> tuple[str, str]:
    """Read an `:86:` field into (payee, memo)."""
    if "?" not in "".join(lines):
        payee, _, memo = " ".join(lines).partition("/")
        return payee.strip(), memo.strip()
    subfields: dict[str, str] = {}
    for part in "".join(lines).split("?")[1:]:
        subfields[part[:2]] = subfields.get(part[:2], "") + part[2:]
    if "32" in subfields:
        payee = subfields["32"] + subfields.get("33", "")
    else:
        payee = subfields.get("00", "")
    memo = "".join(subfields.get(f"2{digit}", "") for digit in range(10))
    return payee, memo


def _decimal(text: str) -> Decimal:
    """Convert an amount with a decimal comma."""
    return Decimal(text.replace(",", "."))


def _format_amount(amount: Decimal) -> str:
    """The absolute amount with a decimal comma and two decimals."""
    return f"{abs(amount):.2f}".replace(".", ",")


def _format_balance(amount: Decimal, day: date, currency: str) -> str:
    """A balance field body: mark, date, currency and amount."""
    mark = "C" if amount >= 0 else "D"
    return f"{mark}{day:%y%m%d}{currency}{_format_amount(amount)}"


def _dump_transaction(t: Transaction) -> list[str]:
    """The `:61:` line and wrapped `:86:` lines for one transaction."""
    if len(t.ref or "") > _MAX_REF_CHARS:
        raise FormatError(f"ref longer than {_MAX_REF_CHARS} characters: {t.ref!r}")
    if "/" in t.payee or "?" in t.payee:
        raise FormatError(f"payee holds '/' or '?': {t.payee!r}")
    mark = "C" if t.amount >= 0 else "D"
    line61 = f":61:{t.day:%y%m%d}{mark}{_format_amount(t.amount)}NTRF{t.ref or _NO_REF}"
    details = f"{t.payee}/{t.memo}" if t.memo else t.payee
    chunks = [details[i : i + _MAX_DETAIL_CHARS] for i in range(0, len(details), _MAX_DETAIL_CHARS)]
    chunks = chunks or [""]
    return [line61, f":86:{chunks[0]}", *chunks[1:]]
