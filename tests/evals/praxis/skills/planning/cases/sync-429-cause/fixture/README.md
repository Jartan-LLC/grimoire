# ordersync

Copies every order from the shop API into `orders.db` each night (`python sync.py`).
The shop API allows 120 requests a minute per key. We have about 5,000 orders.
