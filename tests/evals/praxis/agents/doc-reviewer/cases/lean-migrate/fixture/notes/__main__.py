"""The dev server: list the notes in data/app.db, and add one per POST, on port 8000."""

import http.server
import json
import sqlite3

DB = "data/app.db"


class Notes(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        with sqlite3.connect(DB) as con:
            rows = con.execute("SELECT id, body FROM notes").fetchall()
        self.reply(json.dumps(rows))

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers["Content-Length"])).decode()
        with sqlite3.connect(DB) as con:
            con.execute("INSERT INTO notes (body) VALUES (?)", (body,))
        self.reply("{}")

    def reply(self, text: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(text.encode())


http.server.HTTPServer(("", 8000), Notes).serve_forever()
