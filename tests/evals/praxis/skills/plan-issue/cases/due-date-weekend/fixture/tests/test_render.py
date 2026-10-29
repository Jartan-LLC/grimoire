from datetime import date

from invoicer.render import render


def test_render_totals_and_due_line():
    order = {
        "number": "INV-0042",
        "terms_days": 14,
        "items": [{"name": "Widget", "qty": 3, "unit_cents": 250}],
    }
    text = render(order, date(2026, 3, 6))
    assert "Total" in text
    assert text.endswith("Due: Friday 20 March 2026")
