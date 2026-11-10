# billing-core

PostgreSQL holds `customers`, about 2 million rows. `tax_id_enc` holds each tax ID as a
Fernet token made with `TAX_ID_KEY` from the environment (`billing/crypto.py`).

Three programs decrypt tax IDs, each deployed on its own:

- the API (`billing/api.py`), on four instances replaced one at a time;
- the nightly invoice job (`jobs/invoices.py`);
- the support lookup tool (`support/lookup.py`), released by the support team.
