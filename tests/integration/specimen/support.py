"""Shared helpers and payloads for specimen integration tests."""

BASE = "/api/fhir/v1/specimens"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_specimen(patient_id: int) -> dict:
    return {
        "status": "available",
        "subject": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "type": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "122555007",
                    "display": "Venous blood specimen",
                }
            ],
            "text": "Venous blood",
        },
    }


def full_specimen(patient_id: int) -> dict:
    return {
        "status": "available",
        "type": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "122555007",
                    "display": "Venous blood specimen",
                }
            ],
            "text": "Venous blood",
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "reference_display": "Jane Doe",
        },
        "received_time": "2026-01-01T12:00:00Z",
        "accession_identifier": {
            "use": "official",
            "system": "http://lab.example.org/accession",
            "value": "ACC-2026-001",
            "type_text": "Accession ID",
            "type_coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "ACSN",
                    "display": "Accession ID",
                }
            ],
        },
        "identifier": [
            {
                "use": "usual",
                "system": "http://lab.example.org/specimens",
                "value": "SPEC-001",
                "type_text": "Specimen Identifier",
                "type_coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "PLAC",
                        "display": "Placer Identifier",
                    }
                ],
            }
        ],
        "collection": {
            "collected_date_time": "2026-01-01T11:00:00Z",
            "quantity_value": 10.0,
            "quantity_unit": "mL",
            "quantity_system": "http://unitsofmeasure.org",
            "quantity_code": "mL",
            "method": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "28520004",
                        "display": "Venipuncture",
                    }
                ],
                "text": "Venipuncture",
            },
            "body_site": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "368208006",
                        "display": "Left arm structure",
                    }
                ],
                "text": "Left arm structure",
            },
            "fasting_status_codeable_concept": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0255",
                        "code": "F",
                        "display": "Patient was fasting prior to the procedure.",
                    }
                ],
                "text": "Patient was fasting prior to the procedure.",
            },
        },
        "processing": [
            {
                "description": "Centrifugation",
                "procedure": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "84918000",
                            "display": "Centrifugation",
                        }
                    ],
                    "text": "Centrifugation",
                },
                "time_date_time": "2026-01-01T11:30:00Z",
            }
        ],
        "container": [
            {
                "description": "Red top tube",
                "type": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "706053007",
                            "display": "General specimen container",
                        }
                    ],
                    "text": "Blood tube",
                },
                "capacity_value": 10.0,
                "capacity_unit": "mL",
                "capacity_system": "http://unitsofmeasure.org",
                "capacity_code": "mL",
                "specimen_quantity_value": 8.0,
                "specimen_quantity_unit": "mL",
                "specimen_quantity_system": "http://unitsofmeasure.org",
                "specimen_quantity_code": "mL",
            }
        ],
        "condition": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0493",
                        "code": "FROZ",
                        "display": "Frozen",
                    }
                ],
                "text": "Frozen",
            }
        ],
        "note": [
            {
                "author_string": "Lab Tech",
                "time": "2026-01-01T12:00:00Z",
                "text": "Sample received in good condition.",
            }
        ],
    }


async def create_specimen(client, patient_id: int, **overrides) -> dict:
    payload = minimal_specimen(patient_id)
    payload.update(overrides)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
