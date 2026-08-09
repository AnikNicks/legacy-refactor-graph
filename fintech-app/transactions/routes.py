from flask import Blueprint, jsonify, request

from shared.db import get_db

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/transactions/transfer", methods=["POST"])
def transfer():
    data = request.get_json(force=True)
    from_id = data.get("from_account")
    to_id = data.get("to_account")
    amount = float(data.get("amount", 0))

    db = get_db()

    # The core bug: balances are read, checked, and written back as four
    # separate statements with no row locking and no single atomic
    # transaction wrapping all of it. Two concurrent transfers out of the
    # same account can both read the same starting balance, both pass the
    # sufficient-funds check, and both succeed - a classic double-spend.
    # A crash between the two UPDATE calls below leaves the ledger
    # unbalanced (money leaves one account and never arrives at the other).
    from_row = db.execute("SELECT balance FROM accounts WHERE id = ?", (from_id,)).fetchone()
    if not from_row:
        db.close()
        return jsonify({"error": "unknown from_account"}), 400
    if from_row["balance"] < amount:
        db.close()
        return jsonify({"error": "insufficient funds"}), 400

    to_row = db.execute("SELECT balance FROM accounts WHERE id = ?", (to_id,)).fetchone()
    if not to_row:
        db.close()
        return jsonify({"error": "unknown to_account"}), 400

    new_from_balance = from_row["balance"] - amount
    new_to_balance = to_row["balance"] + amount

    db.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_from_balance, from_id))
    db.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_to_balance, to_id))

    # No idempotency key: a client retry after a network timeout (the
    # transfer actually succeeded, but the response was lost) submits this
    # same request again and moves the money a second time.
    db.execute(
        "INSERT INTO transactions (from_account, to_account, amount, status, created_at) "
        "VALUES (?, ?, ?, 'completed', datetime('now'))",
        (from_id, to_id, amount),
    )
    db.commit()
    db.close()
    return jsonify({"status": "completed", "amount": amount}), 201
