from flask import Flask, request

from app import storage

app = Flask(__name__)


@app.post("/upload")
def upload():
    f = request.files["file"]
    upload_id = storage.save(f.filename, f.read())
    return {"url": storage.url(upload_id, f.filename)}
