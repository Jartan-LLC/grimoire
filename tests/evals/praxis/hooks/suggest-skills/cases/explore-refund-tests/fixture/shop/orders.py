"""Orders and their refunds."""

from dataclasses import dataclass, field


@dataclass
class Order:
    """A paid order."""

    total_cents: int
    refunded_cents: int = 0
    notes: list[str] = field(default_factory=list)

    def refund(self, cents: int) -> None:
        """Give `cents` back, no more than is left."""
        if cents > self.total_cents - self.refunded_cents:
            raise ValueError("refund exceeds what was paid")
        self.refunded_cents += cents
        self.notes.append(f"refunded {cents}")
