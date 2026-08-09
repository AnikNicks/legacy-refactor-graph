from flask import Blueprint, jsonify, request

from shared.db import get_db

records_bp = Blueprint("records", __name__)


@records_bp.route("/records", methods=["POST"])
def add_note():
    data = request.get_json(force=True)
    patient_id = data.get("patient_id")
    note = data.get("note")
    author = data.get("author")

    db = get_db()
    db.execute(
        "INSERT INTO medical_notes (patient_id, note, author, created_at) "
        "VALUES (?, ?, ?, datetime('now'))",
        (patient_id, note, author),
    )
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@records_bp.route("/records/search", methods=["GET"])
def search_notes():
    query = request.args.get("query", "")

    # No access control tied to which provider is searching (backlog - see
    # PROGRESS.md/synthesis for why that's a separate, larger piece of work)
    # and no audit trail yet (that's stage 2).
    db = get_db()
    rows = db.execute(
        "SELECT id, patient_id, note, author, created_at FROM medical_notes "
        "WHERE note LIKE ?",
        (f"%{query}%",),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])
