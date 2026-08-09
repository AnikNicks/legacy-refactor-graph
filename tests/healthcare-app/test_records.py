def _register(client, name="Jane Doe"):
    return client.post(
        "/patients", json={"name": name, "dob": "1990-01-01", "ssn": "1", "phone": "1"}
    ).get_json()["id"]


def test_add_note(client):
    patient_id = _register(client)
    resp = client.post(
        "/records", json={"patient_id": patient_id, "note": "Routine checkup, all normal.", "author": "Dr. Smith"}
    )
    assert resp.status_code == 201


def test_search_finds_note_by_substring(client):
    patient_id = _register(client)
    client.post(
        "/records", json={"patient_id": patient_id, "note": "Routine checkup, all normal.", "author": "Dr. Smith"}
    )

    resp = client.get("/records/search", query_string={"query": "checkup"})
    assert resp.status_code == 200
    results = resp.get_json()
    assert len(results) == 1
    assert results[0]["note"] == "Routine checkup, all normal."


def test_search_returns_notes_for_any_patient_no_access_control(client):
    # Characterizes the current finding: search has no access-control tied
    # to the requesting provider - a note for one patient is returned
    # regardless of who's asking or which patient they're treating.
    patient_a = _register(client, "Patient A")
    patient_b = _register(client, "Patient B")
    client.post("/records", json={"patient_id": patient_a, "note": "shared-term visit", "author": "Dr. A"})
    client.post("/records", json={"patient_id": patient_b, "note": "shared-term follow-up", "author": "Dr. B"})

    resp = client.get("/records/search", query_string={"query": "shared-term"})
    assert len(resp.get_json()) == 2


def test_add_note_with_apostrophe_is_stored_literally(client):
    # Stage 1 fixed this: the INSERT is parameterized now, so an apostrophe
    # is stored as ordinary data instead of crashing the string-formatted
    # query. The flip from "raises" to "succeeds and stores it exactly" is
    # the proof.
    patient_id = _register(client)
    resp = client.post(
        "/records", json={"patient_id": patient_id, "note": "patient's condition improved", "author": "Dr. Smith"}
    )
    assert resp.status_code == 201

    results = client.get("/records/search", query_string={"query": "condition improved"}).get_json()
    assert results[0]["note"] == "patient's condition improved"


def test_search_with_apostrophe_finds_notes_literally(client):
    patient_id = _register(client)
    client.post(
        "/records", json={"patient_id": patient_id, "note": "patient's condition improved", "author": "Dr. Smith"}
    )

    resp = client.get("/records/search", query_string={"query": "patient's"})
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1
