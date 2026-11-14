"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib

CUSTOMERS = [
    {
        "id": 1,
        "email": "ana@example.com",
        "name": "Ana Ruiz",
        "phone": "+34 600 100 200",
        "created": "2021-03-02",
    },
    {"id": 2, "email": "bo@example.com", "name": "Bo Li", "phone": "", "created": "2022-07-19"},
    {
        "id": 3,
        "email": "ana@example.com",
        "name": "Ana Ruiz Diaz",
        "phone": "+34 611 300 400",
        "created": "2024-01-08",
    },
    {
        "id": 4,
        "email": "cy@example.com",
        "name": "Cy Moss",
        "phone": "+44 20 7946 0000",
        "created": "2023-05-30",
    },
    {
        "id": 5,
        "email": "BO@example.com",
        "name": "Bo Li",
        "phone": "+86 10 6552 9988",
        "created": "2025-02-11",
    },
]
data = pathlib.Path("data")
data.mkdir(exist_ok=True)
(data / "customers.json").write_text(json.dumps(CUSTOMERS, indent=2) + "\n")
