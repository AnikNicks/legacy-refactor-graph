from flask import Blueprint, jsonify, request

from shared.db import get_db

records_bp = Blueprint("records", __name__)


def _write_audit_log(action, patient_id=None, query=None, requester=None):
    """Best-effort audit write - never allowed to turn a successful
    operation into an error response, so failures here are swallowed
    intentionally rather than propagated."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO audit_log (action, patient_id, query, requester, created_at) "
            "VALUES (?, ?, ?, ?, datetime('now'))",
            (action, patient_id, query, requester),
        )
        db.commit()
        db.close()
    except Exception:
        pass


@records_bp.route("/records", methods=["POST"])
def add_note():
    data = request.get_json(force=True)
    patient_id = data.get("patient_id")
    note = data.get("note")
    author = data.get("author")
    requester = data.get("requester")

    db = get_db()
    db.execute(
        "INSERT INTO medical_notes (patient_id, note, author, created_at) "
        "VALUES (?, ?, ?, datetime('now'))",
        (patient_id, note, author),
    )
    db.commit()
    db.close()

    try:
        _write_audit_log("add_note", patient_id=patient_id, requester=requester)
    except Exception:
        pass
    return jsonify({"status": "created"}), 201


@records_bp.route("/records/search", methods=["GET"])
def search_notes():
    query = request.args.get("query", "")
    requester = request.args.get("requester")

    # No access control tied to which provider is searching (backlog - see
    # PROGRESS.md/synthesis for why that's a separate, larger piece of work).
    db = get_db()
    rows = db.execute(
        "SELECT id, patient_id, note, author, created_at FROM medical_notes "
        "WHERE note LIKE ?",
        (f"%{query}%",),
    ).fetchall()
    db.close()

    try:
        _write_audit_log("search_notes", query=query, requester=requester)
    except Exception:
        pass
    return jsonify([dict(r) for r in rows])
