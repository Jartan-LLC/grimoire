"""CAMT.053 (ISO 20022 bank-to-customer statement) importer."""

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from xml.parsers import expat
from xml.sax.saxutils import escape, quoteattr

from ledgerkit.model import FormatError, ImportResult, Skipped, Transaction

_NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08"
_SNIFF_MARK = "urn:iso:std:iso:20022:tech:xsd:camt.053."
_SNIFF_WINDOW = 1000
_NOT_PROVIDED = "NOTPROVIDED"
_DAY = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:T.*)?")
_STATUS_SKIPS = {"PDNG": "pending", "INFO": "info"}
_TEXT_ENTITIES = {"\r": "&#13;"}


@dataclass
class _Node:
    """An XML element reduced to what the importer reads."""

    name: str
    line: int
    attrs: dict[str, str]
    text: str = ""
    children: list["_Node"] = field(default_factory=list)

    def kids(self, name: str) -> list["_Node"]:
        """Direct children with this local name."""
        return [c for c in self.children if c.name == name]

    def kid(self, name: str) -> "_Node | None":
        """First direct child with this local name."""
        found = self.kids(name)
        return found[0] if found else None

    def path(self, *names: str) -> "_Node | None":
        """Follow first children down the given names."""
        node: _Node | None = self
        for name in names:
            if node is None:
                return None
            node = node.kid(name)
        return node

    @property
    def value(self) -> str:
        """The element's text without surrounding whitespace."""
        return self.text.strip()


class _Skip(Exception):
    """An entry that cannot become transactions, with the reason."""


def sniff(text: str) -> bool:
    """True when the first 1,000 characters name a CAMT.053 namespace."""
    return _SNIFF_MARK in text[:_SNIFF_WINDOW]


def parse(text: str) -> ImportResult:
    """Read every booked entry of every statement; malformed entries are skipped."""
    result = ImportResult()
    for stmt in _statements(_parse_xml(text)):
        for ntry in stmt.kids("Ntry"):
            try:
                result.transactions.extend(_entry_transactions(ntry))
            except _Skip as skip:
                result.skipped.append(Skipped(ntry.line, str(skip)))
    return result


def dump(transactions: list[Transaction], iban: str = "", statement_id: str = "LEDGERKIT") -> str:
    """Write the transactions as one version 08 statement."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<Document xmlns="{_NAMESPACE}">',
        "  <BkToCstmrStmt>",
        "    <Stmt>",
        f"      <Id>{_esc(statement_id)}</Id>",
        "      <Acct>",
        "        <Id>",
        f"          <IBAN>{_esc(iban)}</IBAN>",
        "        </Id>",
        "      </Acct>",
    ]
    for txn in transactions:
        lines.extend(_dump_entry(txn))
    lines += ["    </Stmt>", "  </BkToCstmrStmt>", "</Document>", ""]
    return "\n".join(lines)


def _esc(text: str) -> str:
    return escape(text, _TEXT_ENTITIES)


def _dump_entry(txn: Transaction) -> list[str]:
    money_out = txn.amount < 0
    lines = [
        "      <Ntry>",
        f"        <Amt Ccy={quoteattr(txn.currency)}>{abs(txn.amount):.2f}</Amt>",
        f"        <CdtDbtInd>{'DBIT' if money_out else 'CRDT'}</CdtDbtInd>",
        "        <Sts><Cd>BOOK</Cd></Sts>",
        f"        <BookgDt><Dt>{txn.day.isoformat()}</Dt></BookgDt>",
        "        <NtryDtls>",
        "          <TxDtls>",
        f"            <Refs><EndToEndId>{_esc(txn.ref or _NOT_PROVIDED)}</EndToEndId></Refs>",
    ]
    if txn.payee:
        party = "Cdtr" if money_out else "Dbtr"
        lines.append(f"            <RltdPties><{party}><Pty><Nm>{_esc(txn.payee)}</Nm></Pty></{party}></RltdPties>")
    if txn.memo:
        lines.append(f"            <RmtInf><Ustrd>{_esc(txn.memo)}</Ustrd></RmtInf>")
    lines += ["          </TxDtls>", "        </NtryDtls>", "      </Ntry>"]
    return lines


def _parse_xml(text: str) -> _Node:
    """Build a namespace-free element tree, recording each start tag's line."""
    parser = expat.ParserCreate()
    stack: list[_Node] = []
    roots: list[_Node] = []

    def start(name: str, attrs: dict[str, str]) -> None:
        node = _Node(name.rpartition(":")[2], parser.CurrentLineNumber, attrs)
        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)
        stack.append(node)

    def end(_name: str) -> None:
        stack.pop()

    def chars(data: str) -> None:
        stack[-1].text += data

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = chars
    try:
        parser.Parse(text, True)
    except expat.ExpatError as err:
        raise FormatError(f"not well-formed XML: {err}") from err
    return roots[0]


def _statements(root: _Node) -> list[_Node]:
    """Every <Stmt> in document order."""
    found = [root] if root.name == "Stmt" else []
    for child in root.children:
        found.extend(_statements(child))
    return found


def _entry_transactions(ntry: _Node) -> list[Transaction]:
    status = _status(ntry)
    if status != "BOOK":
        raise _Skip(_STATUS_SKIPS.get(status, f"status {status}" if status else "missing status"))
    amt = ntry.kid("Amt")
    if amt is None:
        raise _Skip("missing amount")
    amount = _decimal(amt.value)
    indicator = ntry.kid("CdtDbtInd")
    if indicator is None:
        raise _Skip("missing CdtDbtInd")
    if indicator.value not in ("CRDT", "DBIT"):
        raise _Skip(f"bad CdtDbtInd {indicator.value}")
    day = _day(ntry)

    money_out = indicator.value == "DBIT"
    reversal = ntry.kid("RvslInd")
    if reversal is not None and reversal.value.lower() in ("true", "1"):
        sign = 1 if money_out else -1
    else:
        sign = -1 if money_out else 1
    currency = amt.attrs.get("Ccy", "EUR")

    def build(tx: _Node | None, tx_amount: Decimal) -> Transaction:
        return Transaction(
            day=day,
            amount=sign * tx_amount,
            payee=_payee(tx, money_out),
            memo=_memo(ntry, tx),
            ref=_ref(ntry, tx),
            currency=currency,
        )

    txs = [tx for details in ntry.kids("NtryDtls") for tx in details.kids("TxDtls")]
    tx_amounts = [_tx_amount(tx) for tx in txs]
    if len(txs) >= 2 and all(a is not None for a in tx_amounts):
        if sum(tx_amounts, Decimal(0)) != amount:
            raise _Skip("batch does not add up")
        return [build(tx, a) for tx, a in zip(txs, tx_amounts, strict=True)]
    return [build(txs[0] if txs else None, amount)]


def _status(ntry: _Node) -> str:
    node = ntry.kid("Sts")
    if node is None:
        return ""
    code = node.kid("Cd")
    return (code if code is not None else node).value


def _decimal(text: str) -> Decimal:
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise _Skip(f"bad amount {text}") from None
    if not number.is_finite():
        raise _Skip(f"bad amount {text}")
    return number


def _day(ntry: _Node) -> date:
    holder = ntry.kid("BookgDt") or ntry.kid("ValDt")
    stamp = holder and (holder.kid("Dt") or holder.kid("DtTm"))
    if stamp is None:
        raise _Skip("missing date")
    match = _DAY.fullmatch(stamp.value)
    try:
        if match is None:
            raise ValueError
        return date(*map(int, match.groups()[:3]))
    except ValueError:
        raise _Skip(f"bad date {stamp.value}") from None


def _tx_amount(tx: _Node) -> Decimal | None:
    node = tx.kid("Amt") or tx.path("AmtDtls", "TxAmt", "Amt")
    return None if node is None else _decimal(node.value)


def _payee(tx: _Node | None, money_out: bool) -> str:
    if tx is None:
        return ""
    party = tx.path("RltdPties", "Cdtr" if money_out else "Dbtr")
    name = party and (party.kid("Nm") or party.path("Pty", "Nm"))
    return name.value if name else ""


def _memo(ntry: _Node, tx: _Node | None) -> str:
    remittance = tx and tx.kid("RmtInf")
    lines = [u.text for u in remittance.kids("Ustrd") if u.text] if remittance else []
    if lines:
        return " ".join(lines)
    extra = ntry.kid("AddtlNtryInf")
    return extra.value if extra else ""


def _ref(ntry: _Node, tx: _Node | None) -> str | None:
    end_to_end = tx and tx.path("Refs", "EndToEndId")
    if end_to_end and end_to_end.value not in ("", _NOT_PROVIDED):
        return end_to_end.value
    servicer = ntry.kid("AcctSvcrRef")
    return (servicer.value or None) if servicer else None
