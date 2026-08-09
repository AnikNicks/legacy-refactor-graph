from flask import Blueprint, jsonify, request

from shared.db import get_db

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/inventory/<int:product_id>", methods=["GET"])
def get_stock(product_id):
    db = get_db()
    row = db.execute(
        "SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"product_id": product_id, "stock_qty": row["stock_qty"]})


@inventory_bp.route("/inventory/<int:product_id>/adjust", methods=["POST"])
def adjust_stock(product_id):
    data = request.get_json(force=True)
    delta = int(data.get("delta", 0))

    # Not atomic: read the current quantity, compute the new one in Python,
    # then write it back as a separate statement. Two concurrent requests
    # (e.g. two orders decrementing the same product at once) can both read
    # the same starting value and one write clobbers the other - a lost
    # update / overselling bug under real concurrent load.
    db = get_db()
    row = db.execute(
        "SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({"error": "not found"}), 404

    new_qty = row["stock_qty"] + delta
    db.execute(
        "UPDATE inventory SET stock_qty = ? WHERE product_id = ?", (new_qty, product_id)
    )
    db.commit()
    db.close()
    return jsonify({"product_id": product_id, "stock_qty": new_qty})
