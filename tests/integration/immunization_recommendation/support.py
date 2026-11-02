"""Shared helpers and payloads for ImmunizationRecommendation integration tests."""

BASE = "/api/fhir/v1/immunization-recommendations"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"name": "Health Department", "active": True},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_immunization(client, patient_id: int) -> int:
    """Create a minimal immunization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/immunizations/",
        json={
            "status": "completed",
            "vaccine_code": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": "197",
                        "display": "influenza",
                    }
                ],
                "text": "Flu vaccine",
            },
            "patient": {"reference": f"Patient/{patient_id}"},
            "occurrence_date_time": "2025-10-01T10:00:00Z",
            "primary_source": True,
        },
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


def minimal_immunization_recommendation(patient_id: int) -> dict:
    return {
        "patient": {"reference": f"Patient/{patient_id}"},
        "date": "2026-02-01T10:00:00Z",
        "recommendation": [
            {
                "forecast_status": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status",
                            "code": "due",
                            "display": "Due",
                        }
                    ],
                    "text": "Due",
                }
            }
        ],
    }


def full_immunization_recommendation(
    patient_id: int,
    org_id: int | None = None,
    immunization_id: int | None = None,
    condition_id: int | None = None,
) -> dict:
    rec: dict = {
        "vaccine_code": [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": "197",
                        "display": "influenza, high-dose, quadrivalent",
                    }
                ],
                "text": "Fluzone High-Dose Quadrivalent",
            }
        ],
        "target_disease": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "6142004",
                    "display": "Influenza",
                }
            ],
            "text": "Influenza",
        },
        "contraindicated_vaccine_code": [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": "111",
                        "display": "influenza, live, intranasal",
                    }
                ],
                "text": "Live Attenuated Influenza",
            }
        ],
        "forecast_status": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status",
                    "code": "due",
                    "display": "Due",
                }
            ],
            "text": "Due",
        },
        "forecast_reason": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "428191000124101",
                        "display": "Documentation of reason",
                    }
                ],
                "text": "Age 65+",
            }
        ],
        "date_criterion": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "30980-7",
                            "display": "Date vaccine due",
                        }
                    ],
                    "text": "Date vaccine due",
                },
                "value": "2026-02-15T00:00:00Z",
            }
        ],
        "description": "Annual influenza vaccination recommended for older adults",
        "series": "Annual",
        "dose_number_positive_int": 1,
        "series_doses_positive_int": 1,
    }

    if immunization_id:
        rec["supporting_immunization"] = [
            {"reference": f"Immunization/{immunization_id}", "reference_display": "Prior vaccination"}
        ]
    if condition_id:
        rec["supporting_patient_information"] = [
            {"reference": f"Condition/{condition_id}", "reference_display": "Patient condition"}
        ]

    payload: dict = {
        "patient": {"reference": f"Patient/{patient_id}", "reference_display": "Jane Doe"},
        "date": "2026-02-01T10:00:00Z",
        "recommendation": [rec],
    }

    if org_id:
        payload["authority"] = {
            "reference": f"Organization/{org_id}",
            "reference_display": "National Health Authority",
        }
        payload["identifier"] = [
            {
                "use": "official",
                "system": "http://example.org/recommendations",
                "value": "REC-998877",
                "assigner": f"Organization/{org_id}",
            }
        ]

    return payload


async def create_immunization_recommendation(client, patient_id: int) -> int:
    """Create a minimal ImmunizationRecommendation and return its public ID."""
    resp = await client.post(
        BASE + "/", json=minimal_immunization_recommendation(patient_id)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
