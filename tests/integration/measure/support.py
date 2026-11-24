"""Shared helpers and payloads for measure integration tests.

Request bodies are genuine FHIR R4 Measure JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
)

BASE = "/api/fhir/v1/measures"
API = "/api/fhir/v1"

MEASURE_IDS = "https://fhir-server.dev/fhir/identifier-system/measure-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
STATUS_SYSTEM = "http://hl7.org/fhir/publication-status"
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
USAGE_CONTEXT_TYPE = "http://terminology.hl7.org/CodeSystem/usage-context-type"
URL = "https://fhir-server.dev/fhir/Measure/follow-up"


def measure_body(status: str = "active", **extra) -> dict:
    """A valid minimal measure: R4 requires only `status`."""
    return {"status": status, **extra}


def full_body(organization_id: int) -> dict:
    """Every searchable element plus the elements no search parameter reads (they must all
    round-trip: none of them is indexed)."""
    return measure_body(
        resourceType="Measure",
        url=URL,
        identifier=[
            {
                "system": MEASURE_IDS,
                "value": "M-1001",
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
        disclaimer="For research use",
        scoring={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/measure-scoring",
                    "code": "proportion",
                }
            ]
        },
        compositeScoring={"text": "linear"},
        type=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/measure-type",
                        "code": "process",
                    }
                ]
            }
        ],
        riskAdjustment="By age",
        rateAggregation="Weighted average",
        rationale="Reduces readmissions",
        clinicalRecommendationStatement="Follow up within 7 days",
        improvementNotation={"text": "increase"},
        definition=["Readmission: an unplanned return within 30 days"],
        guidance="Use the discharge date",
        group=[
            {
                "id": "g1",
                "code": {"text": "overall"},
                "description": "Overall",
                "population": [
                    {
                        "code": {"text": "initial-population"},
                        "description": "All discharges",
                        "criteria": {
                            "language": "text/cql",
                            "expression": "Initial Population",
                        },
                    },
                    {
                        "code": {"text": "numerator"},
                        "criteria": {"language": "text/cql", "expression": "Numerator"},
                    },
                ],
                "stratifier": [
                    {
                        "code": {"text": "age"},
                        "criteria": {"language": "text/cql", "expression": "AgeGroup"},
                    },
                    {
                        "code": {"text": "multi"},
                        "component": [
                            {
                                "code": {"text": "sex"},
                                "criteria": {
                                    "language": "text/cql",
                                    "expression": "Sex",
                                },
                            },
                            {
                                "code": {"text": "ward"},
                                "criteria": {
                                    "language": "text/cql",
                                    "expression": "Ward",
                                },
                            },
                        ],
                    },
                ],
            }
        ],
        supplementalData=[
            {
                "code": {"text": "race"},
                "usage": [{"text": "supplemental-data"}],
                "criteria": {"language": "text/cql", "expression": "Race"},
            }
        ],
    )


async def create_measure(client, body: dict) -> int:
    """Create a measure and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
