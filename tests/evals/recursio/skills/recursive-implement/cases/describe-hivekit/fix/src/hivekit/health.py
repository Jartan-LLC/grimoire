"""Which hives need attention."""

from datetime import date

from hivekit.log import Inspection, by_hive


def flags(history: list[Inspection]) -> list[str]:
    """The flags of one hive, judged on its latest inspection."""
    latest = history[-1]
    found = []
    if len(history) >= 2 and not (history[-1].queen or history[-2].queen):
        found.append("queenless")
    if latest.brood + latest.honey >= 9:
        found.append("crowded")
    if latest.temper >= 4:
        found.append("defensive")
    return found


def overdue(log: list[Inspection], today: date, days: int = 10) -> list[str]:
    """Hives whose latest inspection is more than `days` days old."""
    return [hive for hive, history in by_hive(log).items() if (today - history[-1].date).days > days]
