# bookapi

The JSON API behind the bookshop's mobile app.

- Python 3.12, standard library only. Each endpoint is a function of the query parameters
  that returns the response body; `bookapi/server.py` maps paths to them.
- Run the tests with `python3 -m pytest -q`.
