DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def weekly_plan(dinners):
    """One dinner per day, in order; `dinners` holds at least seven."""
    return {day: dinners[i % 6] for i, day in enumerate(DAYS)}
