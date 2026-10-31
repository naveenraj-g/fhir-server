"""Shared helpers and payloads for document_reference integration tests."""

BASE = "/api/fhir/v1/document-references"
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
        json={"active": True, "name": [{"family": "Careful", "given": ["Adam"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_document_reference(patient_id: int) -> dict:
    return {
        "status": "current",
        "subject": f"Patient/{patient_id}",
        "content": [
            {
                "attachment": {
                    "url": "https://example.org/docs/1.pdf",
                    "title": "Discharge Summary",
                }
            }
        ],
    }


def full_document_reference(patient_id: int, practitioner_id: int | None = None) -> dict:
    payload = {
        "status": "current",
        "doc_status": "final",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "34108-1",
                    "display": "Outpatient Note",
                }
            ],
            "text": "Outpatient Note",
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
                        "code": "clinical-note",
                        "display": "Clinical Note",
                    }
                ],
                "text": "Clinical Note",
            }
        ],
        "subject": f"Patient/{patient_id}",
        "date": "2026-01-01T12:00:00Z",
        "description": "Follow-up consultation note",
        "security_label": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                        "code": "N",
                        "display": "Normal",
                    }
                ],
                "text": "Normal",
            }
        ],
        "content": [
            {
                "attachment": {
                    "url": "https://example.org/docs/1.pdf",
                    "title": "Consultation Note",
                    "size": 2048,
                },
                "format": {
                    "system": "urn:oid:1.2.840.10008.2.1.1",
                    "code": "urn:ihe:pcc:xphr:2007",
                    "display": "Personal Health Record",
                },
            }
        ],
        "context": {
            "facility_type": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "225732001",
                        "display": "Hospital",
                    }
                ],
                "text": "Hospital",
            },
            "practice_setting": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "408443003",
                        "display": "General medical practice",
                    }
                ],
                "text": "General medical practice",
            },
        },
    }
    if practitioner_id is not None:
        payload["author"] = [f"Practitioner/{practitioner_id}"]
    return payload


async def create_document_reference(client, patient_id: int, **overrides) -> dict:
    payload = minimal_document_reference(patient_id)
    payload.update(overrides)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
