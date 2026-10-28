"""Serve the API: python3 -m bookapi.server."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

from bookapi.authors import list_authors
from bookapi.books import list_books

ROUTES = {"/books": list_books, "/authors": list_authors}


class Handler(BaseHTTPRequestHandler):
    """Answer GET requests from ROUTES."""

    def do_GET(self) -> None:
        url = urlsplit(self.path)
        endpoint = ROUTES.get(url.path)
        if endpoint is None:
            status, body = 404, {"error": "not found"}
        else:
            body = endpoint(dict(parse_qsl(url.query)))
            status = 400 if "error" in body else 200
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())


if __name__ == "__main__":
    ThreadingHTTPServer(("", 8000), Handler).serve_forever()
