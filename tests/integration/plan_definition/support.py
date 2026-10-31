"""Shared helpers and payloads for plan_definition integration tests."""

BASE = "/api/fhir/v1/plan-definitions"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def minimal_plan_definition() -> dict:
    return {
        "status": "draft",
        "name": "DiabetesCarePlanDefinition",
        "title": "Diabetes Care PlanDefinition",
        "experimental": False,
    }


def full_plan_definition() -> dict:
    return {
        "status": "draft",
        "name": "FullPlanDefinition",
        "title": "Full Plan Definition",
        "subtitle": "Comprehensive CDS Protocol",
        "experimental": True,
        "type": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/plan-definition-type",
                    "code": "clinical-protocol",
                    "display": "Clinical Protocol",
                }
            ],
            "text": "Clinical Protocol",
        },
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/plandef",
                "value": "PLANDEF-12345",
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
        "related_artifact": [
            {
                "type": "documentation",
                "label": "Guideline",
                "display": "ADA 2026 Standards of Care",
                "url": "https://diabetesjournals.org/care",
            }
        ],
        "goal": [
            {
                "id": "goal-hba1c",
                "description": {
                    "text": "Target HbA1c < 7.0%",
                },
                "priority": {
                    "text": "high",
                },
            }
        ],
        "action": [
            {
                "id": "act-1",
                "prefix": "1",
                "title": "Initial Assessment",
                "description": "Order initial laboratory tests",
                "priority": "routine",
                "grouping_behavior": "logical-group",
                "selection_behavior": "all",
                "action": [
                    {
                        "id": "act-1-1",
                        "prefix": "1.1",
                        "title": "Order HbA1c",
                        "priority": "routine",
                    }
                ],
            }
        ],
    }


async def create_plan_definition(client, **overrides) -> dict:
    """Helper to create a PlanDefinition and return the response json."""
    payload = minimal_plan_definition()
    payload.update(overrides)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
