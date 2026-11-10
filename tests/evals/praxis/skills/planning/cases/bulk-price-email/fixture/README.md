# acme-mail

One-off customer emails. `make export` writes every customer account to `customers.csv`
(about 40,000 rows; `sample_customers.csv` shows the columns). `scripts/mailer.py` sends a
template to every row of a CSV through Sendwave.

Our Sendwave plan allows 500 messages a minute. Above that it answers 429 and does not
send the message.
