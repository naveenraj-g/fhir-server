"""Shared helpers and payloads for questionnaire_response integration tests.

Request bodies are genuine FHIR R4 QuestionnaireResponse JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

# The resources a QuestionnaireResponse points at (and that point back at it) are created through
# their own routers.
from tests.integration.care_plan.support import (  # noqa: F401
    care_plan_body,
    create_care_plan,
)
from tests.integration.encounter.support import (  # noqa: F401
    create_encounter,
    encounter_body,
)
from tests.integration.group.support import create_group, group_body  # noqa: F401
from tests.integration.observation.support import (  # noqa: F401
    create_observation,
    observation_body,
)
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.procedure.support import (  # noqa: F401
    create_procedure,
    procedure_body,
)
from tests.integration.related_person.support import (  # noqa: F401
    create_related_person,
    related_person_body,
)
from tests.integration.service_request.support import (  # noqa: F401
    create_service_request,
    service_request_body,
)

BASE = "/api/fhir/v1/questionnaire-responses"
API = "/api/fhir/v1"

RESPONSE_IDS = (
    "https://fhir-server.dev/fhir/identifier-system/questionnaire-response-id"
)
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
STATUS_SYSTEM = "http://hl7.org/fhir/questionnaire-answers-status"
SCT = "http://snomed.info/sct"
QUESTIONNAIRE = "https://fhir-server.dev/fhir/Questionnaire/phq-9"

EXTERNAL_PATIENT = {"reference": "https://other.example.org/fhir/Patient/1"}


def questionnaire_response_body(status: str = "completed", **extra) -> dict:
    """A valid minimal questionnaire response: R4 requires only `status`."""
    return {"status": status, **extra}


def full_body(
    organization_id: int,
    patient_id: int,
    practitioner_id: int,
    encounter_id: int,
    care_plan_id: int,
    observation_id: int,
) -> dict:
    """Every R4 element, with an item tree that nests under both `item` and `answer` and uses
    every value[x] kind (they must all round-trip: none of it is indexed)."""
    return questionnaire_response_body(
        resourceType="QuestionnaireResponse",
        identifier={
            "system": RESPONSE_IDS,
            "value": "QR-1001",
            "type": {"coding": [{"system": V2_0203, "code": "ACSN"}]},
            "assigner": {"reference": f"Organization/{organization_id}"},
        },
        basedOn=[{"reference": f"CarePlan/{care_plan_id}"}],
        partOf=[{"reference": f"Observation/{observation_id}"}],
        questionnaire=f"{QUESTIONNAIRE}|1.0",
        subject={"reference": f"Patient/{patient_id}"},
        encounter={"reference": f"Encounter/{encounter_id}"},
        authored="2026-02-01T10:00:00Z",
        author={"reference": f"Practitioner/{practitioner_id}"},
        source={"reference": f"Patient/{patient_id}"},
        item=[
            {
                "linkId": "1",
                "text": "Mood",
                "item": [
                    {
                        "linkId": "1.1",
                        "definition": "http://example.org/definitions/interest",
                        "text": "Little interest or pleasure",
                        "answer": [{"valueInteger": 2}],
                    },
                    {
                        "linkId": "1.2",
                        "answer": [
                            {
                                "valueCoding": {
                                    "system": SCT,
                                    "code": "373066001",
                                    "display": "Yes",
                                },
                                "item": [
                                    {
                                        "linkId": "1.2.1",
                                        "answer": [
                                            {
                                                "valueQuantity": {
                                                    "value": 72.5,
                                                    "comparator": ">",
                                                    "unit": "kg",
                                                    "system": "http://unitsofmeasure.org",
                                                    "code": "kg",
                                                }
                                            },
                                            {
                                                "valueReference": {
                                                    "reference": f"Observation/{observation_id}"
                                                }
                                            },
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                ],
            },
            {
                "linkId": "2",
                "answer": [
                    {"valueBoolean": False},
                    {"valueDecimal": 3.25},
                    {"valueDate": "2026-01-05"},
                    {"valueDateTime": "2026-01-05T08:30:00Z"},
                    {"valueTime": "08:30:00"},
                    {"valueString": "free text"},
                    {"valueUri": "http://example.org/x"},
                    {
                        "valueAttachment": {
                            "contentType": "application/pdf",
                            "url": "https://documents.example.org/scan.pdf",
                            "title": "Scan",
                        }
                    },
                ],
            },
        ],
    )


async def create_questionnaire_response(client, body: dict) -> int:
    """Create a questionnaire response and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
