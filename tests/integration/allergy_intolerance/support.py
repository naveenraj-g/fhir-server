"""Shared helpers and payloads for allergy_intolerance integration tests."""

BASE = "/api/fhir/v1/allergy-intolerances"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_practitioner(client) -> int:
    """Create a minimal practitioner and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/practitioners/",
        json={"active": True, "name": [{"family": "Smith", "given": ["Alice"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_encounter(client, patient_id: int) -> int:
    """Create a minimal encounter and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/encounters/",
        json={
            "status": "in-progress",
            "class_coding": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "subject": f"Patient/{patient_id}",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_allergy_intolerance(patient_id: int) -> dict:
    return {
        "patient": f"Patient/{patient_id}",
        "patient_display": "Jane Doe",
    }


def full_allergy_intolerance(
    patient_id: int,
    practitioner_id: int | None = None,
    encounter_id: int | None = None,
) -> dict:
    payload = {
        "clinical_status": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                    "code": "active",
                    "display": "Active",
                }
            ],
            "text": "Active",
        },
        "verification_status": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                    "code": "confirmed",
                    "display": "Confirmed",
                }
            ],
            "text": "Confirmed",
        },
        "type": "allergy",
        "category": ["food"],
        "criticality": "high",
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "227493005",
                    "display": "Cashew nut allergy",
                }
            ],
            "text": "Cashew nut allergy",
        },
        "patient": f"Patient/{patient_id}",
        "patient_display": "Jane Doe",
        "onset_date_time": "2023-01-15T09:30:00Z",
        "recorded_date": "2023-01-15T10:00:00Z",
        "last_occurrence": "2023-06-01T12:00:00Z",
        "note": [
            {
                "text": "Severe reaction to cashews",
                "time": "2023-01-15T10:05:00Z",
                "author_string": "Dr. Smith",
            }
        ],
        "reaction": [
            {
                "substance": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "227493005",
                            "display": "Cashew nut",
                        }
                    ],
                    "text": "Cashew nut",
                },
                "manifestation": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "64305001",
                                "display": "Urticaria",
                            }
                        ],
                        "text": "Urticaria",
                    }
                ],
                "description": "Facial hives",
                "onset": "2023-01-15T09:40:00Z",
                "severity": "severe",
                "exposure_route": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "26643006",
                            "display": "Oral route",
                        }
                    ],
                    "text": "Oral route",
                },
                "note": [
                    {
                        "text": "EpiPen given",
                        "time": "2023-01-15T10:15:00Z",
                    }
                ],
            }
        ],
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/allergies",
                "value": "ALG-100",
            }
        ],
    }
    if practitioner_id:
        payload["recorder"] = f"Practitioner/{practitioner_id}"
        payload["recorder_display"] = "Dr. Alice Smith"
        payload["asserter"] = f"Practitioner/{practitioner_id}"
        payload["asserter_display"] = "Dr. Alice Smith"
    if encounter_id:
        payload["encounter"] = f"Encounter/{encounter_id}"
        payload["encounter_display"] = "ER Visit"
    return payload


async def create_allergy_intolerance(client, payload: dict | None = None) -> dict:
    """Helper creating an allergy intolerance and asserting 201."""
    if payload is None:
        p_id = await create_test_patient(client)
        payload = minimal_allergy_intolerance(p_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
