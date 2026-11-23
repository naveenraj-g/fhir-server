"""Shared helpers and payloads for questionnaire integration tests.

Request bodies are genuine FHIR R4 Questionnaire JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import create_organization  # noqa: F401
from tests.integration.questionnaire_response.support import (  # noqa: F401
    create_questionnaire_response,
    questionnaire_response_body,
)

BASE = "/api/fhir/v1/questionnaires"
API = "/api/fhir/v1"

QUESTIONNAIRE_IDS = "https://fhir-server.dev/fhir/identifier-system/questionnaire-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
STATUS_SYSTEM = "http://hl7.org/fhir/publication-status"
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
USAGE_CONTEXT_TYPE = "http://terminology.hl7.org/CodeSystem/usage-context-type"
RESOURCE_TYPES = "http://hl7.org/fhir/resource-types"
URL = "https://fhir-server.dev/fhir/Questionnaire/phq-9"


def questionnaire_body(status: str = "active", **extra) -> dict:
    """A valid minimal questionnaire: R4 requires only `status`."""
    return {"status": status, **extra}


def full_body(organization_id: int) -> dict:
    """Every searchable element plus a nested item tree with every enableWhen / answerOption /
    initial value kind (they must all round-trip: none of it is indexed)."""
    return questionnaire_body(
        resourceType="Questionnaire",
        url=URL,
        identifier=[
            {
                "system": QUESTIONNAIRE_IDS,
                "value": "PHQ-9",
                "type": {"coding": [{"system": V2_0203, "code": "ACSN"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        version="1.0",
        name="PHQ9",
        title="Patient Health Questionnaire 9",
        derivedFrom=["https://fhir-server.dev/fhir/Questionnaire/base"],
        experimental=False,
        subjectType=["Patient", "Group"],
        date="2026-01-15T10:00:00Z",
        publisher="Example Health",
        contact=[
            {"name": "Help desk", "telecom": [{"system": "phone", "value": "555-1234"}]}
        ],
        description="A nine-question depression screen.",
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
            {
                "code": {"system": USAGE_CONTEXT_TYPE, "code": "venue"},
                "valueQuantity": {
                    "value": 5,
                    "unit": "mg",
                    "system": UCUM,
                    "code": "mg",
                },
            },
        ],
        jurisdiction=[{"coding": [{"system": "urn:iso:std:iso:3166", "code": "US"}]}],
        purpose="Screening",
        copyright="(c) Example",
        approvalDate="2026-01-10",
        lastReviewDate="2026-01-12",
        effectivePeriod={"start": "2026-01-01", "end": "2026-12-31"},
        code=[{"system": LOINC, "code": "44249-1"}],
        item=[
            {
                "linkId": "1",
                "text": "Mood",
                "type": "group",
                "item": [
                    {
                        "linkId": "1.1",
                        "definition": "http://example.org/definitions/interest",
                        "code": [{"system": LOINC, "code": "44250-9"}],
                        "text": "Little interest or pleasure",
                        "type": "open-choice",
                        "enableBehavior": "any",
                        "enableWhen": [
                            {"question": "1.0", "operator": "=", "answerBoolean": True},
                            {
                                "question": "0.9",
                                "operator": ">=",
                                "answerQuantity": {"value": 5, "comparator": ">"},
                            },
                        ],
                        "required": True,
                        "repeats": False,
                        "readOnly": False,
                        "maxLength": 40,
                        "answerValueSet": "http://example.org/ValueSet/yn",
                        "answerOption": [
                            {
                                "valueCoding": {"system": LOINC, "code": "LA6568-5"},
                                "initialSelected": True,
                            },
                            {"valueString": "other"},
                        ],
                        "initial": [{"valueString": "seed"}],
                    },
                    {
                        "linkId": "1.2",
                        "code": [{"system": LOINC, "code": "44251-7"}],
                        "type": "integer",
                        "initial": [{"valueInteger": 3}],
                    },
                ],
            },
            {
                "linkId": "2",
                "definition": "http://example.org/definitions/second",
                "type": "string",
            },
        ],
    )


async def create_questionnaire(client, body: dict) -> int:
    """Create a questionnaire and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
