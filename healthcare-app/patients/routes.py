from flask import Blueprint, jsonify, request

from shared.db import get_db

patients_bp = Blueprint("patients", __name__)


def _serialize_patient(row, include_sensitive):
    data = {"id": row["id"], "name": row["name"], "phone": row["phone"]}
    if include_sensitive:
        data["ssn"] = row["ssn"]
        data["dob"] = row["dob"]
    return data


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
    # ssn/dob are no longer returned by default - only when the caller
    # explicitly asks via ?include_sensitive=true. This does not add real
    # authorization (there's no auth model to hook into yet - see backlog)
    # but removes PII from the default, most-likely-to-be-called path.
    include_sensitive = request.args.get("include_sensitive") == "true"
    db = get_db()
    row = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(_serialize_patient(row, include_sensitive))


@patients_bp.route("/patients", methods=["GET"])
def list_patients():
    # No pagination, no filtering by requesting provider - every caller sees
    # every patient, not just the ones they're treating (backlog). ssn/dob
    # are excluded by default here too, same as get_patient.
    include_sensitive = request.args.get("include_sensitive") == "true"
    db = get_db()
    rows = db.execute("SELECT * FROM patients").fetchall()
    db.close()
    return jsonify([_serialize_patient(r, include_sensitive) for r in rows])
