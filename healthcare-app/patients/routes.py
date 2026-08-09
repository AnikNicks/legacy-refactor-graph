from flask import Blueprint, jsonify, request

from shared.db import get_db

patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/patients", methods=["POST"])
def register_patient():
    data = request.get_json(force=True)

    # PII (SSN, DOB) logged in plaintext for "debugging" - print() output
    # routinely ends up in log aggregators with far looser access control
    # than the database itself has.
    print(f"[patients] registering patient: {data}")

    db = get_db()
    cur = db.execute(
        "INSERT INTO patients (name, dob, ssn, phone) VALUES (?, ?, ?, ?)",
        (data.get("name"), data.get("dob"), data.get("ssn"), data.get("phone")),
    )
    patient_id = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"id": patient_id}), 201


@patients_bp.route("/patients/<int:patient_id>", methods=["GET"])
def get_patient(patient_id):
    # SELECT * returns every column - including ssn and dob - to any caller
    # who can reach this route at all, regardless of which provider (if any)
    # is actually asking. No field-level authorization exists anywhere in
    # this module.
    db = get_db()
    row = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@patients_bp.route("/patients", methods=["GET"])
def list_patients():
    # No pagination, no filtering by requesting provider - every caller sees
    # every patient's full record, not just the ones they're treating.
    db = get_db()
    rows = db.execute("SELECT * FROM patients").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])
