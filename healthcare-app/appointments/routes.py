import sqlite3

from flask import Blueprint, jsonify, request

from shared.db import get_db

appointments_bp = Blueprint("appointments", __name__)


@appointments_bp.route("/appointments", methods=["POST"])
def schedule_appointment():
    data = request.get_json(force=True)

    # A unique index on (provider, scheduled_at) makes the double-booking
    # check atomic at the database level rather than a separate SELECT then
    # INSERT (which would have the same read-then-write race the other
    # example apps' fixes have been closing all session).
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO appointments (patient_id, provider, scheduled_at, status) "
            "VALUES (?, ?, ?, 'scheduled')",
            (data.get("patient_id"), data.get("provider"), data.get("scheduled_at")),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({"error": "provider already has an appointment at that time"}), 409
    appointment_id = cur.lastrowid
    db.close()
    return jsonify({"id": appointment_id}), 201


@appointments_bp.route("/appointments/<int:patient_id>", methods=["GET"])
def list_appointments(patient_id):
    db = get_db()
    rows = db.execute(
        "SELECT id, provider, scheduled_at, status FROM appointments WHERE patient_id = ?",
        (patient_id,),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])
