"""Shared helpers and payloads for group integration tests.

Request bodies are genuine FHIR R4 Group JSON (camelCase, nested datatypes), and every response
is FHIR R4 too."""

from tests.integration.medication.support import (
    create_medication,
    medication_body,
)
from tests.integration.patient.support import create_patient
from tests.integration.practitioner_role.support import (
    create_organization,
    create_practitioner,
)
from tests.integration.practitioner_role.support import (
    create_role as create_practitioner_role,
)
from tests.integration.related_person.support import (
    create_related_person,
    related_person_body,
)

BASE = "/api/fhir/v1/groups"
API = "/api/fhir/v1"

GROUP_IDS = "https://fhir-server.dev/fhir/identifier-system/group-id"
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


def group_body(**extra) -> dict:
    """A valid minimal Group: R4 requires `type` and `actual`."""
    body = {"type": "person", "actual": True}
    body.update(extra)
    return body


def full_body(
    organization_id: int, patient_id: int, practitioner_id: int, member_group_id: int
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return group_body(
        resourceType="Group",
        identifier=[
            {
                "system": GROUP_IDS,
                "value": "GRP-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        active=True,
        code=concept(SCT, "385093006", "Community"),
        name="Diabetes cohort",
        quantity=3,
        managingEntity={"reference": f"Organization/{organization_id}"},
        characteristic=[
            {
                "code": concept(LOINC, "8302-2", "Body height"),
                "valueRange": {
                    "low": {"value": 150, "unit": "cm"},
                    "high": {"value": 190, "unit": "cm"},
                },
                "exclude": False,
                "period": {"start": "2023-01-01"},
            },
            {
                "code": concept(SCT, "248153007", "Male"),
                "valueBoolean": True,
                "exclude": True,
            },
        ],
        member=[
            {
                "entity": {"reference": f"Patient/{patient_id}"},
                "period": {"start": "2023-01-01"},
                "inactive": False,
            },
            {"entity": {"reference": f"Practitioner/{practitioner_id}"}},
            {"entity": {"reference": f"Group/{member_group_id}"}},
        ],
    )


async def create_group(client, body: dict) -> int:
    """Create a group and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
