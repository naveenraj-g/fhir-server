"""Shared helpers and payloads for episode_of_care integration tests.

Request bodies are genuine FHIR R4 EpisodeOfCare JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

# The resources an EpisodeOfCare points at (and that point back at it) are created through their
# own routers.
from tests.helpers.care_teams import create_minimal_care_team  # noqa: F401
from tests.integration.condition.support import (  # noqa: F401
    condition_body,
    create_condition,
)
from tests.integration.encounter.support import (  # noqa: F401
    create_encounter,
    encounter_body,
)
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.service_request.support import (  # noqa: F401
    create_service_request,
    service_request_body,
)

BASE = "/api/fhir/v1/episodes-of-care"
API = "/api/fhir/v1"

EPISODE_IDS = "https://fhir-server.dev/fhir/identifier-system/episode-of-care-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
EPISODE_TYPE = "http://terminology.hl7.org/CodeSystem/episodeofcare-type"
STATUS_SYSTEM = "http://hl7.org/fhir/episode-of-care-status"
DIAGNOSIS_ROLE = "http://terminology.hl7.org/CodeSystem/diagnosis-role"
SCT = "http://snomed.info/sct"

EXTERNAL_PATIENT = {"reference": "https://other.example.org/fhir/Patient/1"}


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


def episode_body(
    patient_id: int | None = None, status: str = "active", **extra
) -> dict:
    """A valid minimal episode: R4 requires `status` and `patient`. With no patient id the patient
    is an absolute URL (not existence-checked)."""
    patient = (
        {"reference": f"Patient/{patient_id}"} if patient_id else dict(EXTERNAL_PATIENT)
    )
    return {"status": status, "patient": patient, **extra}


def full_body(
    organization_id: int,
    patient_id: int,
    practitioner_id: int,
    condition_id: int,
    service_request_id: int,
    care_team_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return episode_body(
        patient_id,
        resourceType="EpisodeOfCare",
        identifier=[
            {
                "system": EPISODE_IDS,
                "value": "EOC-1001",
                "type": {"coding": [{"system": V2_0203, "code": "MR"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        statusHistory=[
            {
                "status": "planned",
                "period": {"start": "2025-12-01", "end": "2025-12-31"},
            },
            {"status": "active", "period": {"start": "2026-01-01"}},
        ],
        type=[concept(EPISODE_TYPE, "cacp", "Community-based aged care")],
        diagnosis=[
            {
                "condition": {"reference": f"Condition/{condition_id}"},
                "role": concept(DIAGNOSIS_ROLE, "AD", "Admission diagnosis"),
                "rank": 1,
            }
        ],
        managingOrganization={"reference": f"Organization/{organization_id}"},
        period={"start": "2026-01-01", "end": "2026-06-30"},
        referralRequest=[{"reference": f"ServiceRequest/{service_request_id}"}],
        careManager={"reference": f"Practitioner/{practitioner_id}"},
        team=[{"reference": f"CareTeam/{care_team_id}"}],
        account=[{"reference": "https://billing.example.org/fhir/Account/7"}],
    )


async def create_episode(client, body: dict) -> int:
    """Create an episode of care and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
