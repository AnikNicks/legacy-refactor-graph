from flask import Blueprint, jsonify, request

from shared.db import get_db

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/transactions/transfer", methods=["POST"])
def transfer():
    data = request.get_json(force=True)
    from_id = data.get("from_account")
    to_id = data.get("to_account")
    amount = float(data.get("amount", 0))
    idempotency_key = data.get("idempotency_key")
    if not idempotency_key:
        return jsonify({"error": "idempotency_key required"}), 400

    db = get_db()

    # A request with a key we've already completed returns the original
    # result instead of moving money a second time.
    existing = db.execute(
        "SELECT amount FROM transactions WHERE idempotency_key = ?", (idempotency_key,)
    ).fetchone()
    if existing:
        db.close()
        return jsonify({"status": "completed", "amount": existing["amount"]}), 201

    # Confirm the destination exists before touching any balance, so an
    # unknown to_account never debits from_account first.
    to_row = db.execute("SELECT id FROM accounts WHERE id = ?", (to_id,)).fetchone()
    if not to_row:
        db.close()
        return jsonify({"error": "unknown to_account"}), 400

    # Atomic, guarded debit: a single UPDATE with the sufficient-funds check
    # in its own WHERE clause, so sqlite's row locking - not a Python-level
    # read-then-compare - decides whether the debit applies. Two concurrent
    # transfers out of the same account can no longer both succeed off a
    # stale read, and everything here shares one connection/transaction, so
    # a crash before the final commit leaves nothing partially applied.
    cur = db.execute(
        "UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?",
        (amount, from_id, amount),
    )
    if cur.rowcount == 0:
        from_row = db.execute("SELECT balance FROM accounts WHERE id = ?", (from_id,)).fetchone()
        db.close()
        if from_row is None:
            return jsonify({"error": "unknown from_account"}), 400
        return jsonify({"error": "insufficient funds"}), 400

    db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, to_id))

    db.execute(
        "INSERT INTO transactions (from_account, to_account, amount, status, created_at, idempotency_key) "
        "VALUES (?, ?, ?, 'completed', datetime('now'), ?)",
        (from_id, to_id, amount, idempotency_key),
    )
    db.commit()
    db.close()
    return jsonify({"status": "completed", "amount": amount}), 201
