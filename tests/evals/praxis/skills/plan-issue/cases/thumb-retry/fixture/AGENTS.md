# feedreader

Fetches RSS feeds and their item thumbnails for the reading-room display.

- Python 3.12, standard library only.
- Tests: `python3 -m pytest -q`. They never touch the network: patch `urllib.request.urlopen`.
