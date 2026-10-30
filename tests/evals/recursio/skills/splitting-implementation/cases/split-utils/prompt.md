utils.py has turned into a junk drawer. Split it into modules by topic (units, dates, text), keep `pantry.utils` re-exporting the old names so nothing breaks, and point the tests at the new modules.
