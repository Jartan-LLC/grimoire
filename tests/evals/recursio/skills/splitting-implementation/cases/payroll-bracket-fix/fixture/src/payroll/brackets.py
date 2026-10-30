"""Income tax brackets: each slice of annual income is taxed at its own bracket's rate."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

PENNY = Decimal("0.01")


@dataclass(frozen=True)
class Bracket:
    """Income above `lower` and up to and including `upper` (no upper bound when None)."""

    lower: Decimal
    upper: Decimal | None
    rate: Decimal


BRACKETS = (
    Bracket(Decimal("0"), Decimal("12570"), Decimal("0")),
    Bracket(Decimal("12570"), Decimal("50270"), Decimal("0.20")),
    Bracket(Decimal("50270"), Decimal("125140"), Decimal("0.40")),
    Bracket(Decimal("125140"), None, Decimal("0.45")),
)


def bracket_for(income: Decimal) -> Bracket:
    """The bracket `income` falls in; income exactly on an upper bound stays in that bracket."""
    for bracket in BRACKETS:
        if bracket.upper is None or income < bracket.upper:
            return bracket
    raise AssertionError("the last bracket has no upper bound")


def marginal_rate(income: Decimal) -> Decimal:
    """The rate the last pound of `income` pays."""
    return bracket_for(income).rate


def income_tax(income: Decimal) -> Decimal:
    """Annual income tax on `income`, to the penny."""
    tax = Decimal(0)
    for bracket in BRACKETS:
        if income <= bracket.lower:
            break
        top = income if bracket.upper is None else min(income, bracket.upper)
        tax += (top - bracket.lower) * bracket.rate
    return tax.quantize(PENNY, rounding=ROUND_HALF_UP)
