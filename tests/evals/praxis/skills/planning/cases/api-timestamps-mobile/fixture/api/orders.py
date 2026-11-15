"""The orders endpoints."""

from flask import Blueprint, jsonify

from api import store

bp = Blueprint("orders", __name__)


def serialize(order):
    return {
        "id": order["id"],
        "total": order["total"],
        "created_at": int(order["created_at"].timestamp() * 1000),
    }


@bp.get("/orders/<int:order_id>")
def get_order(order_id):
    return jsonify(serialize(store.get(order_id)))
