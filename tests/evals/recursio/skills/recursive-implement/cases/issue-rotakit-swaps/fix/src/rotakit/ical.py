"""Export the rota as an iCalendar file."""

from datetime import timedelta

from rotakit.model import Rota

__all__ = ["to_ical"]


def to_ical(rota: Rota, person: str | None = None) -> str:
    """Every week, or only `person`'s, as iCalendar text with CRLF line ends."""
    names = {p.id: p.name for p in rota.people}
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//rotakit//EN"]
    for week in rota.weeks:
        if person is not None and week.person != person:
            continue
        start = week.start.strftime("%Y%m%d")
        end = (week.start + timedelta(weeks=1)).strftime("%Y%m%d")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{start}-{week.person}@rotakit",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            f"SUMMARY:On call: {names.get(week.person, week.person)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "".join(line + "\r\n" for line in lines)
