def test_register_creates_patient(client):
    resp = client.post(
        "/patients", json={"name": "Jane Doe", "dob": "1990-01-01", "ssn": "123-45-6789", "phone": "555-1234"}
    )
    assert resp.status_code == 201
    assert "id" in resp.get_json()


def test_get_patient_excludes_ssn_dob_by_default(client):
    # Stage 3 fixed the over-exposure finding: the default response no
    # longer includes ssn/dob at all.
    patient_id = client.post(
        "/patients", json={"name": "Jane Doe", "dob": "1990-01-01", "ssn": "123-45-6789", "phone": "555-1234"}
    ).get_json()["id"]

    resp = client.get(f"/patients/{patient_id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "ssn" not in body
    assert "dob" not in body
    assert body["name"] == "Jane Doe"


def test_get_patient_includes_ssn_dob_when_explicitly_requested(client):
    patient_id = client.post(
        "/patients", json={"name": "Jane Doe", "dob": "1990-01-01", "ssn": "123-45-6789", "phone": "555-1234"}
    ).get_json()["id"]

    resp = client.get(f"/patients/{patient_id}", query_string={"include_sensitive": "true"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ssn"] == "123-45-6789"
    assert body["dob"] == "1990-01-01"


def test_get_patient_unknown(client):
    resp = client.get("/patients/999999")
    assert resp.status_code == 404


def test_list_patients_returns_everyone_no_filtering(client):
    # Characterizes the current no-pagination/no-per-provider-filtering
    # finding: every registered patient comes back to any caller.
    client.post("/patients", json={"name": "Jane Doe", "dob": "1990-01-01", "ssn": "1", "phone": "1"})
    client.post("/patients", json={"name": "John Roe", "dob": "1985-05-05", "ssn": "2", "phone": "2"})

    resp = client.get("/patients")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_register_missing_required_name_crashes(client):
    # Characterizes current behavior: the patients table has NOT NULL on
    # name, and register() has no validation before the INSERT, so a
    # missing name raises an uncaught sqlite3.IntegrityError instead of
    # returning a clean 400. Flask's TESTING mode propagates the exception
    # through the test client rather than turning it into a 500 response,
    # so pytest.raises is what actually observes this, not a status code.
    import sqlite3

    import pytest

    with pytest.raises(sqlite3.IntegrityError):
        client.post("/patients", json={"dob": "1990-01-01", "ssn": "1", "phone": "1"})
