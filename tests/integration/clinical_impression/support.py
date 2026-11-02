"""Shared helpers and payloads for ClinicalImpression integration tests."""

BASE = "/api/fhir/v1/clinical-impressions"
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


async def create_test_observation(client, patient_id: int) -> int:
    """Create a minimal observation and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/observations/",
        json={
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8867-4",
                        "display": "Heart rate",
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_risk_assessment(client, patient_id: int) -> int:
    """Create a minimal risk assessment and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/risk-assessments/",
        json={
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_clinical_impression(patient_id: int) -> dict:
    return {
        "status": "completed",
        "subject": {"reference": f"Patient/{patient_id}"},
    }


async def create_clinical_impression(client, patient_id: int) -> int:
    """Create a minimal clinical impression and return its public ID."""
    resp = await client.post(
        f"{BASE}/",
        json=minimal_clinical_impression(patient_id),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def full_clinical_impression(
    patient_id: int,
    encounter_id: int | None = None,
    practitioner_id: int | None = None,
    condition_id: int | None = None,
    observation_id: int | None = None,
    risk_assessment_id: int | None = None,
) -> dict:
    payload = {
        "status": "completed",
        "description": "Initial clinical evaluation for chest pain.",
        "subject": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "effective_date_time": "2026-02-01T10:00:00Z",
        "date": "2026-02-01T11:00:00Z",
        "summary": "Non-cardiac chest pain; musculoskeletal in origin.",
        "status_reason": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/clinicalimpression-status-reason",
                    "code": "treatment-completed",
                    "display": "Treatment Completed",
                }
            ],
            "text": "Evaluation finished and treatment plan established",
        },
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "4241000179101",
                    "display": "Initial evaluation",
                }
            ],
            "text": "Initial acute assessment",
        },
        "protocol": [
            "http://example.org/protocols/chest-pain-eval"
        ],
        "investigation": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "271336007",
                            "display": "Examination / signs",
                        }
                    ],
                    "text": "Initial physical exam",
                },
                "item": (
                    [
                        {
                            "reference": f"Observation/{observation_id}",
                            "reference_display": "Vital signs observation",
                        }
                    ]
                    if observation_id
                    else None
                ),
            }
        ],
        "finding": [
            {
                "item_codeable_concept": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "29857009",
                            "display": "Chest pain, unspecified",
                        }
                    ],
                    "text": "Musculoskeletal chest wall tenderness",
                },
                "item_reference": (
                    {
                        "reference": f"Condition/{condition_id}",
                        "reference_display": "Chest pain condition",
                    }
                    if condition_id
                    else None
                ),
                "basis": "Point tenderness on palpation; normal ECG",
            }
        ],
        "prognosis_codeable_concept": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "170968001",
                        "display": "Good prognosis",
                    }
                ],
                "text": "Full recovery expected within 1-2 weeks",
            }
        ],
        "note": [
            {
                "author_string": "Dr. Alice Smith",
                "time": "2026-02-01T11:30:00Z",
                "text": "Advised gentle stretching and NSAIDs as needed.",
            }
        ],
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/ci-ids",
                "value": "CI-2026-001",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number",
                        }
                    ],
                    "text": "Impression ID",
                },
            }
        ],
    }

    if encounter_id:
        payload["encounter"] = {
            "reference": f"Encounter/{encounter_id}",
            "reference_display": "Emergency Visit",
        }
    if practitioner_id:
        payload["assessor"] = {
            "reference": f"Practitioner/{practitioner_id}",
            "reference_display": "Dr. Alice Smith",
        }
    if condition_id:
        payload["problem"] = [
            {
                "reference": f"Condition/{condition_id}",
                "reference_display": "Active chest pain",
            }
        ]
    if risk_assessment_id:
        payload["prognosis_reference"] = [
            {
                "reference": f"RiskAssessment/{risk_assessment_id}",
                "reference_display": "Cardiovascular risk score",
            }
        ]
    if observation_id:
        payload["supporting_info"] = [
            {
                "reference": f"Observation/{observation_id}",
                "reference_display": "Supporting vitals",
            }
        ]

    return payload
