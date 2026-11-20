"""Shared helpers and payloads for procedure integration tests.

Request bodies are genuine FHIR R4 Procedure JSON (camelCase, nested datatypes),
and every response is FHIR R4 too."""

# The resources a Procedure points at (and that point back at it) are created
# through their own routers.
from tests.integration.appointment.support import (  # noqa: F401
    appointment_body,
    create_appointment,
    create_condition,
    participant,
)
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_location,
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.related_person.support import create_related_person, related_person_body  # noqa: F401

BASE = "/api/fhir/v1/procedures"
API = "/api/fhir/v1"

PROC_IDS = "https://fhir-server.dev/fhir/identifier-system/procedure-id"
EVENT_STATUS = "http://hl7.org/fhir/event-status"
SCT = "http://snomed.info/sct"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"


def procedure_body(patient_id: int | None = None, status: str = "completed", **extra) -> dict:
    """A valid minimal Procedure: R4 requires `status` and `subject`. With no patient
    the reference is an absolute URL (not existence-checked)."""
    subject = {"reference": f"Patient/{patient_id}" if patient_id else "https://other.example.org/fhir/Patient/1"}
    return {"status": status, "subject": subject, **extra}


def full_body(patient_id: int, encounter_id: int, practitioner_id: int, organization_id: int, location_id: int) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return procedure_body(
        patient_id,
        resourceType="Procedure",
        identifier=[
            {
                "system": PROC_IDS,
                "value": "PR-1001",
                "type": {"coding": [{"system": V2_0203, "code": "PRN"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        instantiatesCanonical=["http://example.org/fhir/PlanDefinition/appendectomy|1.0"],
        instantiatesUri=["http://example.org/protocols/appendectomy"],
        basedOn=[{"reference": "ServiceRequest/80001"}],
        statusReason={"coding": [{"system": SCT, "code": "416406003", "display": "Procedure discontinued"}]},
        category={"coding": [{"system": SCT, "code": "387713003", "display": "Surgical procedure"}]},
        code={"coding": [{"system": SCT, "code": "80146002", "display": "Appendectomy"}], "text": "Appendix removal"},
        encounter={"reference": f"Encounter/{encounter_id}"},
        performedPeriod={"start": "2023-01-15T09:30:00Z", "end": "2023-01-15T10:45:00Z"},
        recorder={"reference": f"Practitioner/{practitioner_id}"},
        asserter={"reference": f"Practitioner/{practitioner_id}"},
        performer=[
            {
                "function": {"coding": [{"system": SCT, "code": "304292004", "display": "Surgeon"}]},
                "actor": {"reference": f"Practitioner/{practitioner_id}"},
                "onBehalfOf": {"reference": f"Organization/{organization_id}"},
            }
        ],
        location={"reference": f"Location/{location_id}"},
        reasonCode=[{"coding": [{"system": SCT, "code": "74400008", "display": "Appendicitis"}]}],
        bodySite=[{"coding": [{"system": SCT, "code": "66754008", "display": "Appendix"}]}],
        outcome={"coding": [{"system": SCT, "code": "385669000", "display": "Successful"}]},
        report=[{"reference": "DiagnosticReport/110001"}],
        complication=[{"coding": [{"system": SCT, "code": "131148009", "display": "Bleeding"}]}],
        followUp=[{"text": "Review in two weeks"}],
        note=[
            {
                "authorReference": {"reference": f"Practitioner/{practitioner_id}"},
                "time": "2023-01-15T11:00:00Z",
                "text": "Uneventful.",
            }
        ],
        focalDevice=[
            {"action": {"coding": [{"system": SCT, "code": "129338003"}]}, "manipulated": {"reference": "Device/7"}}
        ],
        usedReference=[{"reference": "Device/7"}],
        usedCode=[{"coding": [{"system": SCT, "code": "86174004", "display": "Scalpel"}]}],
    )


async def create_procedure(client, body: dict) -> int:
    """Create a procedure and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
