"""Pure reporting functions over iterables of transactions."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.model import Transaction

__all__ = ["MonthTotals", "by_category", "monthly_totals", "render_text"]

ZERO = Decimal("0")


@dataclass(frozen=True)
class MonthTotals:
    """Income, spending (money out, positive) and their difference for one month."""

    income: Decimal
    spending: Decimal
    net: Decimal


def _month_key(tx: Transaction) -> str:
    return f"{tx.day.year:04d}-{tx.day.month:02d}"


def _single_currency(txs: Iterable[Transaction]) -> list[Transaction]:
    items = list(txs)
    if len({tx.currency for tx in items}) > 1:
        raise ValueError("transactions are in more than one currency")
    return items


def monthly_totals(txs: Iterable[Transaction]) -> dict[str, MonthTotals]:
    """Totals per "YYYY-MM" in calendar order, with zero rows for empty months in between."""
    items = _single_currency(txs)
    if not items:
        return {}

    income: dict[tuple[int, int], Decimal] = defaultdict(lambda: ZERO)
    spending: dict[tuple[int, int], Decimal] = defaultdict(lambda: ZERO)
    for tx in items:
        key = (tx.day.year, tx.day.month)
        if tx.amount > 0:
            income[key] += tx.amount
        elif tx.amount < 0:
            spending[key] -= tx.amount

    first = min((tx.day.year, tx.day.month) for tx in items)
    last = max((tx.day.year, tx.day.month) for tx in items)
    result: dict[str, MonthTotals] = {}
    year, month = first
    while (year, month) <= last:
        inc = income[(year, month)]
        spent = spending[(year, month)]
        result[f"{year:04d}-{month:02d}"] = MonthTotals(inc, spent, inc - spent)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return result


def by_category(
    txs: Iterable[Transaction], month: str | None = None
) -> list[tuple[str, Decimal]]:
    """Spending per category, largest first then by name, excluding transfers and income."""
    items = _single_currency(txs)
    totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for tx in items:
        if tx.amount >= 0:
            continue
        if month is not None and _month_key(tx) != month:
            continue
        category = tx.category if tx.category is not None else "uncategorized"
        if category.startswith("transfer:"):
            continue
        totals[category] -= tx.amount
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))


def _row(month: str, income: str, spending: str, net: str) -> str:
    return f"{month:<7} {income:>10} {spending:>10} {net:>10}\n"


def render_text(txs: Iterable[Transaction]) -> str:
    """The monthly totals as a fixed-width table with a header line."""
    lines = [_row("Month", "Income", "Spending", "Net")]
    for month, t in monthly_totals(txs).items():
        lines.append(_row(month, f"{t.income:.2f}", f"{t.spending:.2f}", f"{t.net:.2f}"))
    return "".join(lines)
