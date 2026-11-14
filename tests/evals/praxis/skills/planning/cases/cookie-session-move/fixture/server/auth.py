import secrets

from flask import Blueprint, abort, g, jsonify, request

from server.db import db

bp = Blueprint("auth", __name__)
SESSION_DAYS = 30


@bp.post("/api/login")
def login():
    user = db.check_password(request.json["email"], request.json["password"])
    if user is None:
        abort(401)
    token = secrets.token_urlsafe(32)
    db.create_session(token, user["id"], days=SESSION_DAYS)
    return jsonify({"token": token})


@bp.post("/api/logout")
def logout():
    db.delete_session(current_token())
    return "", 204


def current_token():
    return request.headers.get("Authorization", "").removeprefix("Bearer ")


@bp.before_app_request
def load_user():
    g.user = db.user_for_session(current_token())
