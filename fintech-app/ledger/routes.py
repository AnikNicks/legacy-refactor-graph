from flask import Blueprint, jsonify

from shared.db import get_db

ledger_bp = Blueprint("ledger", __name__)


@ledger_bp.route("/ledger/<int:account_id>", methods=["GET"])
def account_ledger(account_id):
    db = get_db()
    rows = db.execute(
        "SELECT id, from_account, to_account, amount, status, created_at FROM transactions "
        "WHERE from_account = ? OR to_account = ?",
        (account_id, account_id),
    ).fetchall()
    db.close()

    # amount is integer cents now (stage 3) - relabeled in the response to
    # match accounts/transactions' *_cents field naming.
    result = []
    for r in rows:
        entry = dict(r)
        entry["amount_cents"] = entry.pop("amount")
        result.append(entry)
    return jsonify(result)
