"""Shared helpers and payloads for care_team integration tests.

Request bodies are genuine FHIR R4 CareTeam JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

# The resources a CareTeam points at (and that point back at it) are created through their own
# routers.
from tests.integration.condition.support import (  # noqa: F401
    condition_body,
    create_condition,
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
    create_role as create_practitioner_role,
)
from tests.integration.related_person.support import (  # noqa: F401
    create_related_person,
    related_person_body,
)

BASE = "/api/fhir/v1/care-teams"
API = "/api/fhir/v1"

CARE_TEAM_IDS = "https://fhir-server.dev/fhir/identifier-system/care-team-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"


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


def care_team_body(**extra) -> dict:
    """A valid care team. R4 requires nothing, so the body is whatever is passed."""
    return dict(extra)


def full_body(
    organization_id: int,
    patient_id: int,
    practitioner_id: int,
    encounter_id: int,
    condition_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return care_team_body(
        resourceType="CareTeam",
        identifier=[
            {
                "system": CARE_TEAM_IDS,
                "value": "CT-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        status="active",
        category=[concept(LOINC, "LA27976-2", "Encounter-focused care team")],
        name="Cardiology care team",
        subject={"reference": f"Patient/{patient_id}"},
        encounter={"reference": f"Encounter/{encounter_id}"},
        period={"start": "2026-01-01", "end": "2026-06-30"},
        participant=[
            {
                "role": [concept(SCT, "17561000", "Cardiologist")],
                "member": {"reference": f"Practitioner/{practitioner_id}"},
                "onBehalfOf": {"reference": f"Organization/{organization_id}"},
                "period": {"start": "2026-01-01"},
            },
        ],
        reasonCode=[concept(SCT, "84114007", "Heart failure")],
        reasonReference=[{"reference": f"Condition/{condition_id}"}],
        managingOrganization=[{"reference": f"Organization/{organization_id}"}],
        telecom=[{"system": "phone", "value": "+1-555-0100", "use": "work"}],
        note=[
            {
                "authorReference": {"reference": f"Practitioner/{practitioner_id}"},
                "time": "2026-02-01T10:00:00Z",
                "text": "Weekly review.",
            }
        ],
    )


async def create_care_team(client, body: dict) -> int:
    """Create a care team and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
