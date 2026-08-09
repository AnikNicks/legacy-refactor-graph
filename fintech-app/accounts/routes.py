from flask import Blueprint, jsonify, request

from shared.db import get_db

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/accounts", methods=["POST"])
def create_account():
    data = request.get_json(force=True)
    # Balance stored (and handled everywhere downstream) as a float, not
    # integer cents - binary floating point can't represent most decimal
    # amounts exactly, so balances drift by fractions of a cent over enough
    # operations.
    starting_balance = float(data.get("starting_balance", 0))

    db = get_db()
    cur = db.execute(
        "INSERT INTO accounts (owner, balance) VALUES (?, ?)",
        (data.get("owner"), starting_balance),
    )
    account_id = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"id": account_id, "balance": starting_balance}), 201


@accounts_bp.route("/accounts/<int:account_id>", methods=["GET"])
def get_account(account_id):
    db = get_db()
    row = db.execute("SELECT id, owner, balance FROM accounts WHERE id = ?", (account_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))
