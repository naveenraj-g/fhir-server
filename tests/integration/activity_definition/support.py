"""Shared helpers and payloads for activity_definition integration tests."""

BASE = "/api/fhir/v1/activity-definitions"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def minimal_activity_definition() -> dict:
    return {
        "status": "draft",
        "name": "BloodGlucoseMonitoringActivity",
        "title": "Blood Glucose Monitoring Activity",
        "kind": "ServiceRequest",
        "intent": "order",
        "priority": "routine",
        "do_not_perform": False,
    }


def full_activity_definition() -> dict:
    return {
        "status": "draft",
        "name": "FullActivityDefinition",
        "title": "Full Activity Definition",
        "subtitle": "Subtitle test",
        "experimental": True,
        "kind": "ServiceRequest",
        "intent": "order",
        "priority": "routine",
        "do_not_perform": False,
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "35335000",
                    "display": "Blood glucose measurement",
                }
            ],
            "text": "Blood glucose measurement",
        },
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/actdef",
                "value": "ACTDEF-12345",
            }
        ],
        "contact": [
            {
                "name": "Clinical Committee",
                "telecom": [
                    {
                        "system": "email",
                        "value": "committee@example.org",
                        "use": "work",
                    }
                ],
            }
        ],
        "use_context": [
            {
                "code_system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
                "code_code": "venue",
                "code_display": "Clinical Venue",
                "value_codeable_concept_text": "Inpatient",
            }
        ],
        "jurisdiction": [
            {
                "coding": [
                    {
                        "system": "urn:iso:std:iso:3166",
                        "code": "US",
                        "display": "United States",
                    }
                ],
                "text": "US",
            }
        ],
        "topic": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "394583002",
                        "display": "Endocrinology",
                    }
                ],
                "text": "Endocrinology",
            }
        ],
        "participant": [
            {
                "type": "practitioner",
                "role": {
                    "text": "Primary Nurse",
                },
            }
        ],
        "dosage": [
            {
                "sequence": 1,
                "text": "Take 1 tablet daily",
                "patient_instruction": "Take with food",
            }
        ],
        "body_site": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "368208006",
                        "display": "Left upper arm structure",
                    }
                ],
                "text": "Left Arm",
            }
        ],
        "related_artifact": [
            {
                "type": "documentation",
                "label": "Guideline",
                "display": "ADA 2026 Standards of Care",
                "url": "https://diabetesjournals.org/care",
            }
        ],
        "dynamic_value": [
            {
                "expression_description": "Dynamic priority",
                "path": "priority",
                "expression_language": "text/cql",
                "expression_expression": "CalculatePriority()",
            }
        ],
    }


async def create_activity_definition(client, **overrides) -> dict:
    """Helper to create an ActivityDefinition and return the response json."""
    payload = minimal_activity_definition()
    payload.update(overrides)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
