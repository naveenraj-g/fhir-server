"""Shared helpers and payloads for activity_definition integration tests.

Request bodies are genuine FHIR R4 ActivityDefinition JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
)

BASE = "/api/fhir/v1/activity-definitions"
API = "/api/fhir/v1"

ACTIVITY_DEFINITION_IDS = (
    "https://fhir-server.dev/fhir/identifier-system/activity-definition-id"
)
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
STATUS_SYSTEM = "http://hl7.org/fhir/publication-status"
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
USAGE_CONTEXT_TYPE = "http://terminology.hl7.org/CodeSystem/usage-context-type"
URL = "https://fhir-server.dev/fhir/ActivityDefinition/follow-up"


def activity_definition_body(status: str = "active", **extra) -> dict:
    """A valid minimal activity definition: R4 requires only `status`."""
    return {"status": status, **extra}


def full_body(organization_id: int) -> dict:
    """Every searchable element plus the elements no search parameter reads (they must all
    round-trip: none of them is indexed)."""
    return activity_definition_body(
        resourceType="ActivityDefinition",
        url=URL,
        identifier=[
            {
                "system": ACTIVITY_DEFINITION_IDS,
                "value": "AD-1001",
                "type": {"coding": [{"system": V2_0203, "code": "ACSN"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        version="1.0",
        name="FollowUp",
        title="Follow-up visit",
        subtitle="Book it",
        experimental=False,
        subjectCodeableConcept={"text": "adults"},
        date="2026-01-15T10:00:00Z",
        publisher="Example Health",
        contact=[
            {"name": "Help desk", "telecom": [{"system": "phone", "value": "555-1234"}]}
        ],
        description="Book a follow-up visit.",
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
        purpose="Follow-up",
        usage="Use after discharge",
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
        kind="ServiceRequest",
        profile="http://example.org/fhir/StructureDefinition/my-request",
        code={"coding": [{"system": LOINC, "code": "44249-1"}]},
        intent="order",
        priority="routine",
        doNotPerform=False,
        timingTiming={"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
        participant=[{"type": "practitioner", "role": {"text": "nurse"}}],
        productCodeableConcept={"text": "saline"},
        quantity={"value": 2, "unit": "mL"},
        dosage=[{"sequence": 1, "text": "2 mL once", "route": {"text": "oral"}}],
        bodySite=[{"text": "arm"}],
        transform="http://example.org/fhir/StructureMap/t1",
        dynamicValue=[
            {
                "path": "priority",
                "expression": {"language": "text/cql", "expression": "Urgent()"},
            }
        ],
    )


async def create_activity_definition(client, body: dict) -> int:
    """Create an activity definition and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
