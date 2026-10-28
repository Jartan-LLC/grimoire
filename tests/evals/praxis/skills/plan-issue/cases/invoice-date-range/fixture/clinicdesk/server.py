"""The HTTP server: python3 -m clinicdesk.server."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

from clinicdesk.bookings import list_bookings
from clinicdesk.errors import BadRequest
from clinicdesk.invoices import list_invoices

ROUTES = {"/bookings": list_bookings, "/invoices": list_invoices}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urlsplit(self.path)
        route = ROUTES.get(url.path)
        if route is None:
            self._send(404, {"error": "not found"})
            return
        try:
            self._send(200, route(dict(parse_qsl(url.query))))
        except BadRequest as error:
            self._send(400, {"error": str(error)})

    def _send(self, status: int, body: object) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
