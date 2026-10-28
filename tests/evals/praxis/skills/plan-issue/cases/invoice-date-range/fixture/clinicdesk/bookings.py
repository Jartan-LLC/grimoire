"""GET /bookings."""

from datetime import date

from clinicdesk import db
from clinicdesk.errors import BadRequest

MAX_DAYS = 92


def list_bookings(query: dict[str, str]) -> list[dict]:
    """Bookings by day; `from` and `to` (YYYY-MM-DD, both inclusive) narrow them to a range."""
    try:
        start = date.fromisoformat(query["from"]) if "from" in query else date.min
        end = date.fromisoformat(query["to"]) if "to" in query else date.max
    except ValueError:
        raise BadRequest("from and to must be dates as YYYY-MM-DD") from None
    if start > end:
        raise BadRequest("from must not be after to")
    if "from" in query and "to" in query and (end - start).days > MAX_DAYS:
        raise BadRequest(f"a range can span at most {MAX_DAYS} days")
    rows = [b for b in db.BOOKINGS if start <= date.fromisoformat(b["day"]) <= end]
    return sorted(rows, key=lambda b: b["day"])
