"""Shared helpers and payloads for Immunization integration tests."""

BASE = "/api/fhir/v1/immunizations"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
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


async def create_test_practitioner(client) -> int:
    """Create a minimal practitioner and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/practitioners/",
        json={"active": True, "name": [{"family": "Smith", "given": ["Alice"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_location(client) -> int:
    """Create a minimal location and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/locations/",
        json={"name": "Immunization Clinic Room 1", "status": "active"},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"name": "Moderna US", "active": True},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


def minimal_immunization(patient_id: int) -> dict:
    return {
        "status": "completed",
        "vaccine_code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "207",
                    "display": "COVID-19, mRNA, LNP-S, PF, 100 mcg/0.5mL dose",
                }
            ],
            "text": "COVID-19 mRNA",
        },
        "patient": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "occurrence_date_time": "2026-01-15T10:00:00Z",
        "primary_source": True,
    }


def full_immunization(
    patient_id: int,
    condition_id: int | None = None,
    practitioner_id: int | None = None,
    location_id: int | None = None,
    org_id: int | None = None,
) -> dict:
    payload = {
        "status": "completed",
        "status_reason": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                    "code": "MEDPREC",
                    "display": "medical precaution",
                }
            ],
            "text": "Medical precaution cleared",
        },
        "vaccine_code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "207",
                    "display": "COVID-19, mRNA, LNP-S, PF, 100 mcg/0.5mL dose",
                }
            ],
            "text": "COVID-19 mRNA",
        },
        "patient": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "occurrence_date_time": "2026-01-15T10:00:00Z",
        "recorded": "2026-01-15T10:05:00Z",
        "primary_source": True,
        "report_origin": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-origin",
                    "code": "recall",
                    "display": "Parent/Guardian/Patient Recall",
                }
            ],
            "text": "Parent Recall",
        },
        "lot_number": "LOT-9988",
        "expiration_date": "2027-01-01",
        "site": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                    "code": "LA",
                    "display": "Left Arm",
                }
            ],
            "text": "Left Arm",
        },
        "route": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
                    "code": "IM",
                    "display": "Intramuscular",
                }
            ],
            "text": "Intramuscular",
        },
        "dose_quantity": {
            "value": 0.5,
            "unit": "mL",
            "system": "http://unitsofmeasure.org",
            "code": "mL",
        },
        "is_subpotent": False,
        "funding_source": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-funding-source",
                    "code": "private",
                    "display": "Private",
                }
            ],
            "text": "Private Insurance",
        },
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/immunizations",
                "value": "IMM-2026-001",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number",
                        }
                    ],
                    "text": "MRN",
                },
            }
        ],
        "performer": [
            {
                "actor": {
                    "reference": f"Practitioner/{practitioner_id}" if practitioner_id else "Practitioner/30001",
                    "reference_display": "Dr. Alice Smith",
                },
                "function": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
                            "code": "AP",
                            "display": "Administering Provider",
                        }
                    ],
                    "text": "Administering Provider",
                },
            }
        ],
        "note": [
            {
                "text": "Routine vaccination administered smoothly.",
                "time": "2026-01-15T10:05:00Z",
            }
        ],
        "reason_code": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "429060002",
                        "display": "Procedure to produce and evaluate active immunity",
                    }
                ],
                "text": "Annual vaccine",
            }
        ],
        "subpotent_reason": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-subpotent-reason",
                        "code": "partialdose",
                        "display": "Partial Dose",
                    }
                ],
                "text": "Partial Dose",
            }
        ],
        "education": [
            {
                "document_type": "VIS",
                "publication_date": "2025-08-06T00:00:00Z",
                "presentation_date": "2026-01-15T00:00:00Z",
                "reference": "https://www.cdc.gov/vaccines/hcp/vis/vis-statements/covid-19.pdf",
            }
        ],
        "program_eligibility": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-program-eligibility",
                        "code": "ineligible",
                        "display": "Not Eligible",
                    }
                ],
                "text": "Not Eligible",
            }
        ],
        "reaction": [
            {
                "date": "2026-01-15T10:30:00Z",
                "reported": True,
            }
        ],
        "protocol_applied": [
            {
                "series": "COVID-19 Primary Series",
                "dose_number_positive_int": 1,
                "series_doses_positive_int": 2,
                "target_disease": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "840539006",
                                "display": "COVID-19",
                            }
                        ],
                        "text": "COVID-19",
                    }
                ],
            }
        ],
    }

    if location_id:
        payload["location"] = {
            "reference": f"Location/{location_id}",
            "reference_display": "Immunization Clinic Room 1",
        }
    if org_id:
        payload["manufacturer"] = {
            "reference": f"Organization/{org_id}",
            "reference_display": "Moderna US",
        }
    if condition_id:
        payload["reason_reference"] = [
            {
                "reference": f"Condition/{condition_id}",
                "reference_display": "High risk condition",
            }
        ]

    return payload


async def create_immunization(client, payload: dict) -> int:
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
