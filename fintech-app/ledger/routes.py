from flask import Blueprint, jsonify

from shared.db import get_db

ledger_bp = Blueprint("ledger", __name__)


@ledger_bp.route("/ledger/<account_id>", methods=["GET"])
def account_ledger(account_id):
    db = get_db()
    # String-formatted SQL - the same injection family that shows up in the
    # other example apps, kept here too so risk-assessor has a consistent
    # finding type to compare across every example.
    rows = db.execute(
        "SELECT id, from_account, to_account, amount, status, created_at FROM transactions "
        "WHERE from_account = %s OR to_account = %s" % (account_id, account_id)
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
