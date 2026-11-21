"""Shared helpers and payloads for family_member_history integration tests.

Request bodies are genuine FHIR R4 FamilyMemberHistory JSON (camelCase, nested datatypes),
and every response is FHIR R4 too."""

# The resources a FamilyMemberHistory points at (and that point back at it) are created
# through their own routers.
from tests.integration.allergy_intolerance.support import allergy_body, create_allergy_intolerance  # noqa: F401
from tests.integration.condition.support import condition_body, create_condition  # noqa: F401
from tests.integration.diagnostic_report.support import create_report, report_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)

BASE = "/api/fhir/v1/family-member-histories"
API = "/api/fhir/v1"

HISTORY_IDS = "https://fhir-server.dev/fhir/identifier-system/family-member-history-id"
STATUS_SYSTEM = "http://hl7.org/fhir/history-status"
ROLE_CODE = "http://terminology.hl7.org/CodeSystem/v3-RoleCode"
GENDER = "http://hl7.org/fhir/administrative-gender"
SCT = "http://snomed.info/sct"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"

MOTHER = {"coding": [{"system": ROLE_CODE, "code": "MTH", "display": "mother"}]}


def relationship(code: str = "MTH", display: str | None = None) -> dict:
    return {"coding": [{"system": ROLE_CODE, "code": code, **({"display": display} if display else {})}]}


def sex(code: str = "female") -> dict:
    return {"coding": [{"system": GENDER, "code": code}]}


def disease(code: str, display: str | None = None) -> dict:
    return {"coding": [{"system": SCT, "code": code, **({"display": display} if display else {})}]}


def history_body(patient_id: int | None = None, status: str = "completed", **extra) -> dict:
    """A valid minimal FamilyMemberHistory: R4 requires `status`, `patient` and `relationship`.
    With no patient the reference is an absolute URL (not existence-checked)."""
    patient = {"reference": f"Patient/{patient_id}" if patient_id else "https://other.example.org/fhir/Patient/1"}
    return {"status": status, "patient": patient, "relationship": MOTHER, **extra}


def full_body(patient_id: int, organization_id: int, practitioner_id: int, condition_id: int) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return history_body(
        patient_id,
        resourceType="FamilyMemberHistory",
        identifier=[
            {
                "system": HISTORY_IDS,
                "value": "FMH-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        instantiatesCanonical=["http://example.org/fhir/PlanDefinition/family-history|1.0"],
        instantiatesUri=["http://example.org/protocols/family-history"],
        dataAbsentReason={"coding": [{"system": "http://terminology.hl7.org/CodeSystem/history-absent-reason", "code": "withheld"}]},
        date="2023-01-15T09:30:00Z",
        name="Mary Windsor",
        relationship=relationship("MTH", "mother"),
        sex=sex("female"),
        ageAge={"value": 70, "unit": "yr", "system": "http://unitsofmeasure.org", "code": "a"},
        estimatedAge=True,
        deceasedBoolean=False,
        reasonCode=[{"coding": [{"system": SCT, "code": "160303001", "display": "Family history of diabetes"}]}],
        reasonReference=[{"reference": f"Condition/{condition_id}"}, {"reference": "Observation/160001"}],
        note=[{"text": "Since her forties", "time": "2023-01-15T10:00:00Z", "authorString": "Nurse Joy"}],
        condition=[
            {
                "code": disease("44054006", "Type 2 diabetes mellitus"),
                "outcome": disease("6736007", "Moderate"),
                "contributedToDeath": False,
                "onsetAge": {"value": 42, "unit": "yr", "system": "http://unitsofmeasure.org", "code": "a"},
                "note": [{"text": "Insulin from 55", "authorReference": {"reference": f"Practitioner/{practitioner_id}"}}],
            },
            {"code": disease("38341003", "Hypertension"), "onsetString": "in her fifties"},
        ],
    )


async def create_history(client, body: dict) -> int:
    """Create a family member history and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
