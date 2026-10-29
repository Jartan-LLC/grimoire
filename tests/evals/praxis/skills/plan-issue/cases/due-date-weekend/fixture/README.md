# invoicer

Turns an order into invoice text with a number, line items, totals and a due date.

```bash
python3 -m invoicer order.json
```

Payment terms come from the customer record (`terms_days`, 14 by default). A due date
that falls on a weekend moves to the next Monday.
