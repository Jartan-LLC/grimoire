"""Where uploads are written and how their links are made."""

import pathlib
import uuid

ROOT = pathlib.Path("/srv/uploads")


def save(name, data):
    upload_id = uuid.uuid4().hex
    folder = ROOT / upload_id
    folder.mkdir(parents=True)
    (folder / name).write_bytes(data)
    return upload_id


def url(upload_id, name):
    return f"/uploads/{upload_id}/{name}"
