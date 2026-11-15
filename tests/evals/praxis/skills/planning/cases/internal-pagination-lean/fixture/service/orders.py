from flask import Blueprint, jsonify

from service import db

bp = Blueprint("orders", __name__)


@bp.get("/internal/orders")
def list_orders():
    return jsonify(db.all_orders())
