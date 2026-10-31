"""How much honey the hives hold."""

from datetime import date

from hivekit.log import Inspection

FRAME_KG = 2.0


def honey_kg(inspection: Inspection) -> float:
    """The inspection's honey in kilograms."""
    return inspection.honey * FRAME_KG


def gains(history: list[Inspection]) -> list[tuple[date, float]]:
    """The change in honey from each inspection to the next."""
    return [(b.date, honey_kg(b) - honey_kg(a)) for a, b in zip(history, history[1:], strict=False)]
