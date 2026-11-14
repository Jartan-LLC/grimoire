from flask import Blueprint, abort, g, request

from server.db import db

bp = Blueprint("payouts", __name__)


@bp.post("/api/payouts/destination")
def set_destination():
    if g.user is None:
        abort(401)
    db.set_payout_account(g.user["id"], request.json["iban"])
    return "", 204
