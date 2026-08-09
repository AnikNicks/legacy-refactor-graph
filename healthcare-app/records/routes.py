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
    # String-concatenated SQL, the same injection family as a generic web
    # app - but here the table being written to holds clinical notes, which
    # raises the severity of the same code smell considerably.
    db.execute(
        "INSERT INTO medical_notes (patient_id, note, author, created_at) "
        "VALUES (%s, '%s', '%s', datetime('now'))" % (patient_id, note, author)
    )
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@records_bp.route("/records/search", methods=["GET"])
def search_notes():
    query = request.args.get("query", "")

    # Same injection smell on the read path, and - separately - no access
    # control tied to which provider is searching: any caller can search
    # every patient's clinical notes. No audit trail is written anywhere in
    # this module even though every call here touches PII/PHI.
    db = get_db()
    rows = db.execute(
        "SELECT id, patient_id, note, author, created_at FROM medical_notes "
        "WHERE note LIKE '%%%s%%'" % query
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])
