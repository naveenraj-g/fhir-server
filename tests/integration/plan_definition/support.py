"""Shared helpers and payloads for plan_definition integration tests.

Request bodies are genuine FHIR R4 PlanDefinition JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
)

BASE = "/api/fhir/v1/plan-definitions"
API = "/api/fhir/v1"

PLAN_DEFINITION_IDS = (
    "https://fhir-server.dev/fhir/identifier-system/plan-definition-id"
)
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
STATUS_SYSTEM = "http://hl7.org/fhir/publication-status"
PD_TYPE = "http://terminology.hl7.org/CodeSystem/plan-definition-type"
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
USAGE_CONTEXT_TYPE = "http://terminology.hl7.org/CodeSystem/usage-context-type"
URL = "https://fhir-server.dev/fhir/PlanDefinition/discharge-pathway"


def plan_definition_body(status: str = "active", **extra) -> dict:
    """A valid minimal plan definition: R4 requires only `status`."""
    return {"status": status, **extra}


def full_body(organization_id: int) -> dict:
    """Every searchable element plus the elements no search parameter reads (they must all
    round-trip: none of them is indexed), including a nested action tree."""
    return plan_definition_body(
        resourceType="PlanDefinition",
        url=URL,
        identifier=[
            {
                "system": PLAN_DEFINITION_IDS,
                "value": "PD-1001",
                "type": {"coding": [{"system": V2_0203, "code": "ACSN"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        version="1.0",
        name="DischargePathway",
        title="Discharge pathway",
        subtitle="After surgery",
        type={"coding": [{"system": PD_TYPE, "code": "clinical-protocol"}]},
        experimental=False,
        subjectCodeableConcept={"text": "adults"},
        date="2026-01-15T10:00:00Z",
        publisher="Example Health",
        contact=[
            {"name": "Help desk", "telecom": [{"system": "phone", "value": "555-1234"}]}
        ],
        description="Steps to take at discharge.",
        useContext=[
            {
                "code": {"system": USAGE_CONTEXT_TYPE, "code": "focus"},
                "valueCodeableConcept": {
                    "coding": [
                        {"system": SCT, "code": "35489007", "display": "Depression"}
                    ]
                },
            },
            {
                "code": {"system": USAGE_CONTEXT_TYPE, "code": "age"},
                "valueRange": {
                    "low": {"value": 12, "system": UCUM, "code": "a"},
                    "high": {"value": 17, "system": UCUM, "code": "a"},
                },
            },
        ],
        jurisdiction=[{"coding": [{"system": "urn:iso:std:iso:3166", "code": "US"}]}],
        purpose="Discharge",
        usage="Use at discharge",
        copyright="(c) Example",
        approvalDate="2026-01-10",
        lastReviewDate="2026-01-12",
        effectivePeriod={"start": "2026-01-01", "end": "2026-12-31"},
        topic=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/definition-topic",
                        "code": "treatment",
                    }
                ]
            }
        ],
        author=[{"name": "Dr A"}],
        editor=[{"name": "Dr B"}],
        reviewer=[{"name": "Dr C"}],
        endorser=[{"name": "Dr D"}],
        relatedArtifact=[
            {
                "type": "documentation",
                "display": "Guide",
                "url": "http://example.org/g",
            },
            {
                "type": "composed-of",
                "resource": "http://example.org/fhir/Library/x|1.0",
            },
        ],
        library=["http://example.org/fhir/Library/lib1"],
        goal=[
            {
                "id": "g1",
                "category": {"text": "behavioral"},
                "description": {"text": "Walk daily"},
                "priority": {"text": "high"},
                "start": {"text": "discharge"},
                "target": [
                    {
                        "measure": {"text": "steps"},
                        "detailRange": {
                            "low": {"value": 4000},
                            "high": {"value": 8000},
                        },
                        "due": {"value": 30, "unit": "d"},
                    }
                ],
            }
        ],
        action=[
            {
                "id": "a1",
                "title": "Discharge checks",
                "groupingBehavior": "logical-group",
                "selectionBehavior": "all",
                "goalId": ["g1"],
                "condition": [
                    {
                        "kind": "applicability",
                        "expression": {"language": "text/cql", "expression": "Adult()"},
                    }
                ],
                "action": [
                    {
                        "title": "Book a visit",
                        "definitionCanonical": "http://example.org/fhir/ActivityDefinition/visit|1.0",
                        "relatedAction": [
                            {"actionId": "a1", "relationship": "after-end"}
                        ],
                        "timingDuration": {"value": 1, "unit": "d"},
                    },
                    {
                        "title": "Fill a form",
                        "definitionCanonical": "http://example.org/fhir/Questionnaire/form",
                        "dynamicValue": [
                            {
                                "path": "title",
                                "expression": {
                                    "language": "text/fhirpath",
                                    "expression": "'x'",
                                },
                            }
                        ],
                    },
                ],
            }
        ],
    )


async def create_plan_definition(client, body: dict) -> int:
    """Create a plan definition and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
