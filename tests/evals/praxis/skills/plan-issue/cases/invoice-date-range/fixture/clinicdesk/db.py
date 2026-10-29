"""The clinic's records (an in-memory stand-in for the database)."""

BOOKINGS = [
    {"id": 1, "day": "2026-10-05", "patient": "R. Ahmed", "therapist": "Lena"},
    {"id": 2, "day": "2026-10-06", "patient": "J. Novak", "therapist": "Marc"},
    {"id": 3, "day": "2026-10-14", "patient": "R. Ahmed", "therapist": "Lena"},
]

INVOICES = [
    {"number": "2026-101", "day": "2026-10-05", "patient": "R. Ahmed", "total_cents": 6500},
    {"number": "2026-102", "day": "2026-10-06", "patient": "J. Novak", "total_cents": 6500},
    {"number": "2026-103", "day": "2026-10-14", "patient": "R. Ahmed", "total_cents": 4500},
]
