"""Parse a rainfall file."""

from datetime import date

from plantkit.model import GardenError


def parse_rain(text: str) -> dict[date, float]:
    """Millimetres of rain per date; a date given twice adds up."""
    rain: dict[date, float] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if number == 1 or not line.strip():
            continue
        fields = [field.strip() for field in line.split(",")]
        try:
            if len(fields) != 2:
                raise ValueError("expected date,mm")
            day, mm = date.fromisoformat(fields[0]), float(fields[1])
            if mm < 0:
                raise ValueError("rain cannot be negative")
        except ValueError as error:
            raise GardenError(f"line {number}: {error}") from error
        rain[day] = rain.get(day, 0.0) + mm
    return rain
