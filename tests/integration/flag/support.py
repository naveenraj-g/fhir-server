"""Shared helpers and payloads for flag integration tests.

Request bodies are genuine FHIR R4 Flag JSON (camelCase, nested datatypes), and every response is
FHIR R4 too."""

from tests.integration.encounter.support import (  # noqa: F401
    create_encounter,
    encounter_body,
)
from tests.integration.group.support import create_group, group_body  # noqa: F401
from tests.integration.medication.support import (  # noqa: F401
    create_medication,
    medication_body,
)
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_location,
    create_organization,
    create_practitioner,
)

BASE = "/api/fhir/v1/flags"
API = "/api/fhir/v1"

FLAG_IDS = "https://fhir-server.dev/fhir/identifier-system/flag-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
FLAG_CATEGORY = "http://terminology.hl7.org/CodeSystem/flag-category"


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


def flag_body(subject: dict | None = None, **extra) -> dict:
    """A valid minimal Flag: R4 requires `status`, `code` and `subject`. With no `subject` given
    the subject is an absolute URL (not existence-checked)."""
    return {
        "status": "active",
        "code": {"text": "Patient has a latex allergy"},
        "subject": subject or {"reference": "https://other.example.org/fhir/Patient/1"},
        **extra,
    }


def full_body(
    patient_id: int, encounter_id: int, practitioner_id: int, organization_id: int
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return flag_body(
        {"reference": f"Patient/{patient_id}"},
        resourceType="Flag",
        identifier=[
            {
                "system": FLAG_IDS,
                "value": "F-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        status="active",
        category=[concept(FLAG_CATEGORY, "safety", "Safety")],
        code=concept("http://snomed.info/sct", "300916003", "Latex allergy"),
        period={"start": "2026-01-15", "end": "2026-12-31"},
        encounter={"reference": f"Encounter/{encounter_id}"},
        author={"reference": f"Practitioner/{practitioner_id}"},
    )


async def create_flag(client, body: dict) -> int:
    """Create a flag and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
