"""Shared helpers and payloads for task integration tests.

Request bodies are genuine FHIR R4 Task JSON (camelCase, nested datatypes), and every response is
FHIR R4 too."""

from tests.integration.encounter.support import (  # noqa: F401
    create_encounter,
    encounter_body,
)
from tests.integration.group.support import create_group, group_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_location,
    create_organization,
    create_practitioner,
)
from tests.integration.service_request.support import (  # noqa: F401
    create_service_request,
    service_request_body,
)

BASE = "/api/fhir/v1/tasks"
API = "/api/fhir/v1"

TASK_IDS = "https://fhir-server.dev/fhir/identifier-system/task-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
TASK_CODE = "http://hl7.org/fhir/CodeSystem/task-code"
BUSINESS = "http://example.org/business-status"
PERFORMER = "http://terminology.hl7.org/CodeSystem/task-performer-type"


def concept(system: str, code: str, display: str | None = None) -> dict:
    return {
        "coding": [
            {
                "system": system,
                "code": code,
                **({"display": display} if display else {}),
            }
        ]
    }


def task_body(**extra) -> dict:
    """A valid minimal Task: R4 requires `status` and `intent`."""
    return {"status": "requested", "intent": "order", **extra}


def full_body(
    patient_id: int,
    encounter_id: int,
    practitioner_id: int,
    organization_id: int,
    location_id: int,
    service_request_id: int,
    parent_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return task_body(
        resourceType="Task",
        identifier=[
            {
                "system": TASK_IDS,
                "value": "T-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        instantiatesCanonical="http://example.org/ActivityDefinition/collect|1.0",
        instantiatesUri="http://example.org/protocols/collect",
        basedOn=[{"reference": f"ServiceRequest/{service_request_id}"}],
        groupIdentifier={"system": TASK_IDS, "value": "GRP-1"},
        partOf=[{"reference": f"Task/{parent_id}"}],
        status="in-progress",
        statusReason=concept("http://example.org/reasons", "waiting"),
        businessStatus=concept(BUSINESS, "specimen-collected", "Specimen collected"),
        intent="order",
        priority="urgent",
        code=concept(TASK_CODE, "fulfill", "Fulfill the focal request"),
        description="Collect a blood sample",
        focus={"reference": f"ServiceRequest/{service_request_id}"},
        encounter={"reference": f"Encounter/{encounter_id}"},
        executionPeriod={
            "start": "2026-01-15T09:00:00Z",
            "end": "2026-01-15T10:00:00Z",
        },
        authoredOn="2026-01-15T08:00:00Z",
        lastModified="2026-01-15T09:30:00Z",
        requester={"reference": f"Practitioner/{practitioner_id}"},
        performerType=[concept(PERFORMER, "performer", "Performer")],
        owner={"reference": f"Practitioner/{practitioner_id}"},
        location={"reference": f"Location/{location_id}"},
        reasonCode={"text": "routine collection"},
        reasonReference={"reference": f"Patient/{patient_id}"},
        insurance=[{"reference": "Coverage/9"}],
        note=[{"text": "Fasting required", "time": "2026-01-15T08:00:00Z"}],
        relevantHistory=[{"reference": "Provenance/9"}],
        restriction={
            "repetitions": 2,
            "period": {"end": "2026-02-15T00:00:00Z"},
            "recipient": [{"reference": f"Patient/{patient_id}"}],
        },
        input=[
            {"type": {"text": "sample type"}, "valueString": "venous blood"},
            {"type": {"text": "volume"}, "valueQuantity": {"value": 5, "unit": "mL"}},
            {"type": {"text": "fasting"}, "valueBoolean": True},
        ],
        output=[
            {
                "type": {"text": "result"},
                "valueReference": {"reference": f"Patient/{patient_id}"},
            }
        ],
        **{"for": {"reference": f"Patient/{patient_id}"}},
    )


async def create_task(client, body: dict) -> int:
    """Create a task and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
