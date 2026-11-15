"""The upload endpoint the share sheet posts to."""

from http.server import BaseHTTPRequestHandler
from pathlib import Path

from snapbox.store import UploadRefused, save_upload


def make_handler(root: Path) -> type[BaseHTTPRequestHandler]:
    """A handler class that saves POST /upload bodies under `root`."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != "/upload":
                self.send_error(404)
                return
            name = self.headers.get("X-Filename", "")
            data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            try:
                saved = save_upload(root, name, data)
            except UploadRefused as refused:
                self._reply(400, str(refused))
                return
            self._reply(201, saved.name)

        def _reply(self, status: int, text: str) -> None:
            body = text.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler
