"""Shared helpers and payloads for RiskAssessment integration tests."""

BASE = "/api/fhir/v1/risk-assessments"
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


async def create_test_condition(client, patient_id: int) -> int:
    """Create a minimal condition and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/conditions/",
        json={
            "clinical_status": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "verification_status": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
        },
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


def minimal_risk_assessment(patient_id: int) -> dict:
    return {
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
    }


async def create_risk_assessment(client, patient_id: int) -> int:
    """Create a minimal risk assessment and return its public ID."""
    resp = await client.post(
        f"{BASE}/",
        json=minimal_risk_assessment(patient_id),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def full_risk_assessment(
    patient_id: int,
    condition_id: int | None = None,
    practitioner_id: int | None = None,
    encounter_id: int | None = None,
) -> dict:
    payload = {
        "status": "final",
        "subject": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "occurrence_date_time": "2026-02-01T10:00:00Z",
        "method": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "709510001",
                    "display": "Framingham risk score",
                    "user_selected": True,
                }
            ],
            "text": "Framingham 10-year risk assessment",
        },
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "89243-0",
                    "display": "Cardiovascular disease 10Y risk [Likelihood]",
                    "user_selected": True,
                }
            ],
            "text": "Cardiovascular disease 10Y risk",
        },
        "reason_code": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "171121004",
                        "display": "Screening for cardiovascular disease",
                        "user_selected": True,
                    }
                ],
                "text": "Screening for cardiovascular disease",
            }
        ],
        "prediction": [
            {
                "outcome": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "49436004",
                            "display": "Atrial fibrillation",
                            "user_selected": True,
                        }
                    ],
                    "text": "Atrial fibrillation",
                },
                "probability_decimal": 0.12,
                "qualitative_risk": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                            "code": "moderate",
                            "display": "Moderate likelihood",
                            "user_selected": True,
                        }
                    ],
                    "text": "Moderate risk",
                },
                "relative_risk": 1.5,
                "when_period": {
                    "start": "2026-02-01T10:00:00Z",
                    "end": "2036-02-01T10:00:00Z",
                },
                "rationale": "Elevated systolic BP and family history.",
            }
        ],
        "mitigation": "Lifestyle modifications and low-dose antihypertensive therapy.",
        "note": [
            {
                "text": "Re-evaluate in 12 months.",
                "time": "2026-02-01T10:00:00Z",
                "author_string": "Dr. Alice Smith",
            }
        ],
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/risk-assessment-ids",
                "value": "RA-2026-001",
                "period_start": "2026-02-01T10:00:00Z",
                "period_end": "2027-02-01T10:00:00Z",
            }
        ],
    }

    if condition_id is not None:
        payload["condition"] = {
            "reference": f"Condition/{condition_id}",
            "reference_display": "Hypertension",
        }
        payload["reason_reference"] = [
            {
                "reference": f"Condition/{condition_id}",
                "reference_display": "Hypertension",
            }
        ]

    if practitioner_id is not None:
        payload["performer"] = {
            "reference": f"Practitioner/{practitioner_id}",
            "reference_display": "Dr. Alice Smith",
        }

    if encounter_id is not None:
        payload["encounter"] = {
            "reference": f"Encounter/{encounter_id}",
            "reference_display": "Annual Physical",
        }

    return payload
