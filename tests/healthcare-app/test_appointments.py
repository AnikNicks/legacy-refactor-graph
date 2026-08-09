def _register(client):
    return client.post(
        "/patients", json={"name": "Jane Doe", "dob": "1990-01-01", "ssn": "1", "phone": "1"}
    ).get_json()["id"]


def test_schedule_appointment(client):
    patient_id = _register(client)
    resp = client.post(
        "/appointments", json={"patient_id": patient_id, "provider": "Dr. Smith", "scheduled_at": "2026-08-10T10:00"}
    )
    assert resp.status_code == 201


def test_list_appointments_for_patient(client):
    patient_id = _register(client)
    client.post(
        "/appointments", json={"patient_id": patient_id, "provider": "Dr. Smith", "scheduled_at": "2026-08-10T10:00"}
    )

    resp = client.get(f"/appointments/{patient_id}")
    assert resp.status_code == 200
    appts = resp.get_json()
    assert len(appts) == 1
    assert appts[0]["provider"] == "Dr. Smith"


def test_double_booking_same_provider_same_slot_is_rejected(client):
    # Stage 5 fixed this: the second request for the same provider/slot is
    # now rejected (409) instead of both silently succeeding.
    patient_a = _register(client)
    patient_b = _register(client)
    slot = {"provider": "Dr. Smith", "scheduled_at": "2026-08-10T10:00"}

    first = client.post("/appointments", json={**slot, "patient_id": patient_a})
    second = client.post("/appointments", json={**slot, "patient_id": patient_b})

    assert first.status_code == 201
    assert second.status_code == 409


def test_same_provider_different_time_still_succeeds(client):
    patient_a = _register(client)
    patient_b = _register(client)

    first = client.post(
        "/appointments", json={"patient_id": patient_a, "provider": "Dr. Smith", "scheduled_at": "2026-08-10T10:00"}
    )
    second = client.post(
        "/appointments", json={"patient_id": patient_b, "provider": "Dr. Smith", "scheduled_at": "2026-08-10T11:00"}
    )
    assert first.status_code == 201
    assert second.status_code == 201


def test_different_provider_same_time_still_succeeds(client):
    patient_a = _register(client)
    patient_b = _register(client)

    first = client.post(
        "/appointments", json={"patient_id": patient_a, "provider": "Dr. Smith", "scheduled_at": "2026-08-10T10:00"}
    )
    second = client.post(
        "/appointments", json={"patient_id": patient_b, "provider": "Dr. Jones", "scheduled_at": "2026-08-10T10:00"}
    )
    assert first.status_code == 201
    assert second.status_code == 201
