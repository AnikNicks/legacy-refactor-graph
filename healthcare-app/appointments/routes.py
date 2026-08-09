from flask import Blueprint, jsonify, request

from shared.db import get_db

appointments_bp = Blueprint("appointments", __name__)


@appointments_bp.route("/appointments", methods=["POST"])
def schedule_appointment():
    data = request.get_json(force=True)

    # No check for the same provider already having an appointment at this
    # time - two patients can be booked with the same provider in the same
    # slot with nothing here to catch it.
    db = get_db()
    cur = db.execute(
        "INSERT INTO appointments (patient_id, provider, scheduled_at, status) "
        "VALUES (?, ?, ?, 'scheduled')",
        (data.get("patient_id"), data.get("provider"), data.get("scheduled_at")),
    )
    appointment_id = cur.lastrowid
    db.commit()
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
