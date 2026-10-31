"""OFX importer: reads OFX 1.x (SGML) and 2.x (XML), writes OFX 2.x."""

import re
from collections import Counter
from datetime import date
from decimal import Decimal
from itertools import islice

from ledgerkit.model import FormatError, ImportResult, Skipped, Transaction

DEFAULT_CURRENCY = "EUR"
NAME_LIMIT = 32

_TAG = re.compile(r"<(/?)([A-Za-z][\w.]*)[^>]*>")
_DTPOSTED = re.compile(r"(\d{4})(\d{2})(\d{2})(?:\d{6}(?:\.\d+)?)?(?:\[[^\]]*\])?")
_TRNAMT = re.compile(r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)")
_ENTITY = re.compile(r"&(amp|lt|gt);")
_ENTITY_CHARS = {"amp": "&", "lt": "<", "gt": ">"}
_FIELDS = {
    ("", "DTPOSTED"): "date",
    ("", "TRNAMT"): "amount",
    ("", "NAME"): "name",
    ("PAYEE", "NAME"): "payee_name",
    ("", "MEMO"): "memo",
    ("", "FITID"): "ref",
    ("CURRENCY", "CURSYM"): "currency",
}
_HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>\n'
)


def sniff(text: str) -> bool:
    """True when the first non-blank line is an OFX 1.x header or `<?OFX` is in the first five lines."""
    first = next((line for line in text.splitlines() if line.strip()), "")
    return first.lstrip().startswith("OFXHEADER:") or "<?OFX" in "\n".join(islice(text.splitlines(), 5))


def parse(text: str) -> ImportResult:
    """Read every `<STMTTRN>` of every statement, in file order.

    Raises:
        FormatError: If the text has no `<OFX>` element.
    """
    tags = list(_TAG.finditer(text))
    if not any(not m[1] and m[2].upper() == "OFX" for m in tags):
        raise FormatError("no <OFX> element")
    result = ImportResult()
    seen_refs: set[str] = set()
    currency = DEFAULT_CURRENCY
    fields: dict[str, str] | None = None
    section = ""
    opened_line = 0
    for m, following in zip(tags, [*tags[1:], None]):
        name = m[2].upper()
        if m[1]:
            if name == "STMTTRN" and fields is not None:
                _finish(fields, currency, opened_line, seen_refs, result)
                fields = None
            elif name in ("PAYEE", "CURRENCY"):
                section = ""
        elif name == "STMTTRN":
            fields = {}
            opened_line = text.count("\n", 0, m.start()) + 1
        elif name in ("STMTRS", "CCSTMTRS"):
            currency = DEFAULT_CURRENCY
        elif name in ("PAYEE", "CURRENCY"):
            section = name
        else:
            value = _unescape(text[m.end() : following.start() if following else len(text)].strip())
            if name == "CURDEF" and fields is None:
                currency = value
            elif fields is not None and (key := _FIELDS.get((section, name))):
                fields.setdefault(key, value)
    return result


def dump(transactions: list[Transaction], account: str = "0000") -> str:
    """Write the transactions as OFX 2.x, one statement per currency.

    Raises:
        FormatError: If two transactions end up with the same FITID.
    """
    fitids = _fitids(transactions)
    by_currency: dict[str, list[tuple[Transaction, str]]] = {}
    for transaction, fitid in zip(transactions, fitids):
        by_currency.setdefault(transaction.currency, []).append((transaction, fitid))
    lines = [*_HEADER.splitlines(), "<OFX>", "  <BANKMSGSRSV1>"]
    for currency, items in by_currency.items():
        lines += _statement(currency, items, account)
    lines += ["  </BANKMSGSRSV1>", "</OFX>"]
    return "\n".join(lines) + "\n"


def _unescape(value: str) -> str:
    """Decode `&amp;`, `&lt;` and `&gt;`."""
    return _ENTITY.sub(lambda m: _ENTITY_CHARS[m[1]], value)


def _escape(value: str) -> str:
    """Encode `&`, `<` and `>` as entities."""
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _finish(
    fields: dict[str, str], currency: str, line: int, seen_refs: set[str], result: ImportResult
) -> None:
    """Turn one collected `<STMTTRN>` into a transaction or a `Skipped`."""
    try:
        transaction = _build(fields, currency)
    except ValueError as error:
        result.skipped.append(Skipped(line, str(error)))
        return
    if transaction.ref is not None:
        if transaction.ref in seen_refs:
            result.skipped.append(Skipped(line, f"duplicate FITID {transaction.ref}"))
            return
        seen_refs.add(transaction.ref)
    result.transactions.append(transaction)


def _build(fields: dict[str, str], currency: str) -> Transaction:
    """Build a transaction from collected fields; ValueError carries the skip reason."""
    return Transaction(
        day=_parse_day(fields.get("date")),
        amount=_parse_amount(fields.get("amount")),
        payee=fields.get("name") or fields.get("payee_name", ""),
        memo=fields.get("memo", ""),
        ref=fields.get("ref") or None,
        currency=fields.get("currency") or currency,
    )


def _parse_day(value: str | None) -> date:
    """Read the date part of a DTPOSTED value."""
    if not value:
        raise ValueError("missing DTPOSTED")
    match = _DTPOSTED.fullmatch(value)
    if match is None:
        raise ValueError(f"bad DTPOSTED {value}")
    try:
        return date(*map(int, match.groups()))
    except ValueError:
        raise ValueError(f"bad DTPOSTED {value}") from None


def _parse_amount(value: str | None) -> Decimal:
    """Read a TRNAMT value with a decimal point or comma."""
    if not value:
        raise ValueError("missing TRNAMT")
    if _TRNAMT.fullmatch(value) is None:
        raise ValueError(f"bad TRNAMT {value}")
    return Decimal(value.replace(",", "."))


def _fitids(transactions: list[Transaction]) -> list[str]:
    """The FITID of each transaction: its ref, or `<day>-<n>`; FormatError on repeats."""
    per_day: Counter[date] = Counter()
    fitids: list[str] = []
    for transaction in transactions:
        if transaction.ref is None:
            per_day[transaction.day] += 1
            fitids.append(f"{transaction.day:%Y%m%d}-{per_day[transaction.day]}")
        else:
            fitids.append(transaction.ref)
    repeated = [fitid for fitid, count in Counter(fitids).items() if count > 1]
    if repeated:
        raise FormatError(f"duplicate ref {repeated[0]}")
    return fitids


def _statement(currency: str, items: list[tuple[Transaction, str]], account: str) -> list[str]:
    """The lines of one `<STMTTRNRS>` holding the given transactions."""
    days = [t.day for t, _ in items]
    lines = [
        "    <STMTTRNRS>",
        "      <STMTRS>",
        f"        <CURDEF>{_escape(currency)}</CURDEF>",
        "        <BANKACCTFROM>",
        f"          <ACCTID>{_escape(account)}</ACCTID>",
        "        </BANKACCTFROM>",
        "        <BANKTRANLIST>",
        f"          <DTSTART>{min(days):%Y%m%d}</DTSTART>",
        f"          <DTEND>{max(days):%Y%m%d}</DTEND>",
    ]
    for transaction, fitid in items:
        lines += _entry(transaction, fitid)
    return [*lines, "        </BANKTRANLIST>", "      </STMTRS>", "    </STMTTRNRS>"]


def _entry(transaction: Transaction, fitid: str) -> list[str]:
    """The lines of one `<STMTTRN>`."""
    pad = " " * 10
    lines = [
        f"{pad}<STMTTRN>",
        f"{pad}  <TRNTYPE>{'CREDIT' if transaction.amount >= 0 else 'DEBIT'}</TRNTYPE>",
        f"{pad}  <DTPOSTED>{transaction.day:%Y%m%d}</DTPOSTED>",
        f"{pad}  <TRNAMT>{transaction.amount.quantize(Decimal('0.01')):f}</TRNAMT>",
        f"{pad}  <FITID>{_escape(fitid)}</FITID>",
        f"{pad}  <NAME>{_escape(transaction.payee[:NAME_LIMIT])}</NAME>",
    ]
    if transaction.memo:
        lines.append(f"{pad}  <MEMO>{_escape(transaction.memo)}</MEMO>")
    lines.append(f"{pad}</STMTTRN>")
    return lines
