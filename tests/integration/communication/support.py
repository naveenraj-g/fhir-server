"""Shared helpers and payloads for communication integration tests.

Request bodies are genuine FHIR R4 Communication JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

from tests.integration.care_team.support import (  # noqa: F401
    care_team_body,
    create_care_team,
)
from tests.integration.encounter.support import (  # noqa: F401
    create_encounter,
    encounter_body,
)
from tests.integration.group.support import create_group, group_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
)
from tests.integration.related_person.support import (  # noqa: F401
    create_related_person,
    related_person_body,
)
from tests.integration.service_request.support import (  # noqa: F401
    create_service_request,
    service_request_body,
)

BASE = "/api/fhir/v1/communications"
API = "/api/fhir/v1"

COMM_IDS = "https://fhir-server.dev/fhir/identifier-system/communication-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
CATEGORY = "http://terminology.hl7.org/CodeSystem/communication-category"
MEDIUM = "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode"
PLAN_DEFINITION = "http://example.org/fhir/PlanDefinition/notify"


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


def communication_body(**extra) -> dict:
    """A valid minimal Communication: R4 requires `status`."""
    return {"status": "completed", **extra}


def full_body(
    patient_id: int,
    encounter_id: int,
    practitioner_id: int,
    organization_id: int,
    service_request_id: int,
    parent_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return communication_body(
        resourceType="Communication",
        identifier=[
            {
                "system": COMM_IDS,
                "value": "CM-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        instantiatesCanonical=[f"{PLAN_DEFINITION}|1.0"],
        instantiatesUri=["http://example.org/protocols/notify"],
        basedOn=[{"reference": f"ServiceRequest/{service_request_id}"}],
        partOf=[{"reference": f"Communication/{parent_id}"}],
        inResponseTo=[{"reference": f"Communication/{parent_id}"}],
        status="completed",
        statusReason=concept("http://example.org/reasons", "done"),
        category=[concept(CATEGORY, "notification", "Notification")],
        priority="urgent",
        medium=[concept(MEDIUM, "WRITTEN", "written")],
        subject={"reference": f"Patient/{patient_id}"},
        topic={"text": "lab results"},
        about=[{"reference": f"Patient/{patient_id}"}],
        encounter={"reference": f"Encounter/{encounter_id}"},
        sent="2026-01-15T09:00:00Z",
        received="2026-01-15T09:05:00Z",
        recipient=[{"reference": f"Patient/{patient_id}"}],
        sender={"reference": f"Practitioner/{practitioner_id}"},
        reasonCode=[{"text": "results ready"}],
        reasonReference=[{"reference": "Device/9"}],
        payload=[
            {"contentString": "Your results are ready."},
            {
                "contentAttachment": {
                    "contentType": "application/pdf",
                    "title": "report",
                }
            },
            {"contentReference": {"reference": f"Patient/{patient_id}"}},
        ],
        note=[{"text": "Sent by post", "time": "2026-01-15T09:00:00Z"}],
    )


async def create_communication(client, body: dict) -> int:
    """Create a communication and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
