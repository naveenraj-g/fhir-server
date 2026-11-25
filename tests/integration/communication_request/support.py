"""Shared helpers and payloads for communication-request integration tests.

Request bodies are genuine FHIR R4 CommunicationRequest JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

from tests.integration.care_team.support import (
    care_team_body,
    create_care_team,
)
from tests.integration.communication.support import (
    communication_body,
    create_communication,
)
from tests.integration.encounter.support import (
    create_encounter,
    encounter_body,
)
from tests.integration.group.support import create_group, group_body
from tests.integration.patient.support import create_patient
from tests.integration.practitioner_role.support import (
    create_organization,
    create_practitioner,
)
from tests.integration.related_person.support import (
    create_related_person,
    related_person_body,
)
from tests.integration.service_request.support import (
    create_service_request,
    service_request_body,
)

BASE = "/api/fhir/v1/communication-requests"
API = "/api/fhir/v1"

CR_IDS = "https://fhir-server.dev/fhir/identifier-system/communication-request-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
CATEGORY = "http://terminology.hl7.org/CodeSystem/communication-category"
MEDIUM = "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode"


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


def communication_request_body(**extra) -> dict:
    """A valid minimal CommunicationRequest: R4 requires `status`."""
    return {"status": "active", **extra}


def full_body(
    patient_id: int,
    encounter_id: int,
    practitioner_id: int,
    organization_id: int,
    service_request_id: int,
    replaced_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return communication_request_body(
        resourceType="CommunicationRequest",
        identifier=[
            {
                "system": CR_IDS,
                "value": "CR-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        basedOn=[{"reference": f"ServiceRequest/{service_request_id}"}],
        replaces=[{"reference": f"CommunicationRequest/{replaced_id}"}],
        groupIdentifier={"system": "urn:groups", "value": "G-1"},
        status="active",
        statusReason=concept("http://example.org/reasons", "approved"),
        category=[concept(CATEGORY, "reminder", "Reminder")],
        priority="urgent",
        doNotPerform=False,
        medium=[concept(MEDIUM, "WRITTEN", "written")],
        subject={"reference": f"Patient/{patient_id}"},
        about=[{"reference": f"Patient/{patient_id}"}],
        encounter={"reference": f"Encounter/{encounter_id}"},
        payload=[
            {"contentString": "Please book your follow-up visit."},
            {
                "contentAttachment": {
                    "contentType": "application/pdf",
                    "title": "leaflet",
                }
            },
            {"contentReference": {"reference": f"Patient/{patient_id}"}},
        ],
        occurrenceDateTime="2026-02-01T09:00:00Z",
        authoredOn="2026-01-15T09:00:00Z",
        requester={"reference": f"Practitioner/{practitioner_id}"},
        recipient=[{"reference": f"Patient/{patient_id}"}],
        sender={"reference": f"Practitioner/{practitioner_id}"},
        reasonCode=[{"text": "follow-up needed"}],
        reasonReference=[{"reference": "Device/9"}],
        note=[{"text": "Call twice", "time": "2026-01-15T09:00:00Z"}],
    )


async def create_communication_request(client, body: dict) -> int:
    """Create a communication request and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
