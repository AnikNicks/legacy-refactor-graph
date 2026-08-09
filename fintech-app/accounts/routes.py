from flask import Blueprint, jsonify, request

from shared.db import get_db

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/accounts", methods=["POST"])
def create_account():
    data = request.get_json(force=True)
    # Integer cents, not a float dollar amount - closes the precision-drift
    # finding at its source. The field name change (starting_balance ->
    # starting_balance_cents) is deliberate: a caller silently sending
    # dollars into a cents-typed field would be a much worse bug than a
    # clean 400 from a renamed, unrecognized field.
    starting_balance_cents = int(data.get("starting_balance_cents", 0))

    db = get_db()
    cur = db.execute(
        "INSERT INTO accounts (owner, balance) VALUES (?, ?)",
        (data.get("owner"), starting_balance_cents),
    )
    account_id = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"id": account_id, "balance_cents": starting_balance_cents}), 201


@accounts_bp.route("/accounts/<int:account_id>", methods=["GET"])
def get_account(account_id):
    db = get_db()
    row = db.execute("SELECT id, owner, balance FROM accounts WHERE id = ?", (account_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": row["id"], "owner": row["owner"], "balance_cents": row["balance"]})
