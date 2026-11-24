"""Shared helpers and payloads for goal integration tests.

Request bodies are genuine FHIR R4 Goal JSON (camelCase, nested datatypes), and every response is
FHIR R4 too."""

from tests.integration.condition.support import (  # noqa: F401
    condition_body,
    create_condition,
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
)

BASE = "/api/fhir/v1/goals"
API = "/api/fhir/v1"

GOAL_IDS = "https://fhir-server.dev/fhir/identifier-system/goal-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
ACHIEVEMENT = "http://terminology.hl7.org/CodeSystem/goal-achievement"
GOAL_CATEGORY = "http://terminology.hl7.org/CodeSystem/goal-category"
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


def goal_body(subject: dict | None = None, **extra) -> dict:
    """A valid minimal Goal: R4 requires `lifecycleStatus`, `description` and `subject`. With no
    `subject` given the subject is an absolute URL (not existence-checked)."""
    return {
        "lifecycleStatus": "active",
        "description": {"text": "Reduce HbA1c below 7%"},
        "subject": subject or {"reference": "https://other.example.org/fhir/Patient/1"},
        **extra,
    }


def full_body(
    patient_id: int,
    organization_id: int,
    condition_id: int,
    observation_id: int,
    practitioner_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return goal_body(
        {"reference": f"Patient/{patient_id}"},
        resourceType="Goal",
        identifier=[
            {
                "system": GOAL_IDS,
                "value": "G-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        lifecycleStatus="active",
        achievementStatus=concept(ACHIEVEMENT, "in-progress", "In Progress"),
        category=[concept(GOAL_CATEGORY, "dietary", "Dietary")],
        priority=concept(
            "http://terminology.hl7.org/CodeSystem/goal-priority", "high-priority"
        ),
        startDate="2026-01-15",
        target=[
            {
                "measure": concept(LOINC, "4548-4", "Hemoglobin A1c"),
                "detailQuantity": {"value": 7, "comparator": "<", "unit": "%"},
                "dueDate": "2026-12-31",
            },
            {
                "measure": concept(LOINC, "29463-7", "Body weight"),
                "detailRange": {"low": {"value": 60}, "high": {"value": 70}},
                "dueDuration": {"value": 6, "unit": "mo"},
            },
        ],
        statusDate="2026-01-20",
        statusReason="Patient agreed",
        expressedBy={"reference": f"Practitioner/{practitioner_id}"},
        addresses=[
            {"reference": f"Condition/{condition_id}"},
            {"reference": "NutritionOrder/9"},
        ],
        note=[{"text": "Agreed with the patient.", "time": "2026-01-15T10:00:00Z"}],
        outcomeCode=[{"text": "improved"}],
        outcomeReference=[{"reference": f"Observation/{observation_id}"}],
    )


async def create_goal(client, body: dict) -> int:
    """Create a goal and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
