"""Shared helpers and payloads for immunization_evaluation integration tests.

Request bodies are genuine FHIR R4 ImmunizationEvaluation JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources an ImmunizationEvaluation points at (and that point back at it) are
# created through their own routers.
from tests.integration.immunization.support import create_immunization, immunization_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import create_organization  # noqa: F401

BASE = "/api/fhir/v1/immunization-evaluations"
API = "/api/fhir/v1"

EVALUATION_IDS = "https://fhir-server.dev/fhir/identifier-system/immunization-evaluation-id"
STATUS_SYSTEM = "http://hl7.org/fhir/event-status"
SCT = "http://snomed.info/sct"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
DOSE_STATUS = "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status"
DOSE_REASON = "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status-reason"

DATE = "2023-01-15T09:30:00Z"
TARGET = {"coding": [{"system": SCT, "code": "6142004", "display": "Influenza"}]}
ABSOLUTE_EVENT = {"reference": "https://other.example.org/fhir/Immunization/1"}


def dose_status(code: str = "valid", **extra) -> dict:
    return {"coding": [{"system": DOSE_STATUS, "code": code, **extra}]}


def evaluation_body(
    patient_id: int | None = None, immunization_id: int | None = None, status: str = "completed", **extra
) -> dict:
    """A valid minimal ImmunizationEvaluation: R4 requires `status`, `patient`, `targetDisease`,
    `immunizationEvent` and `doseStatus`. With no patient / immunization the references are
    absolute URLs (not existence-checked)."""
    patient = {"reference": f"Patient/{patient_id}" if patient_id else "https://other.example.org/fhir/Patient/1"}
    event = {"reference": f"Immunization/{immunization_id}"} if immunization_id else ABSOLUTE_EVENT
    return {
        "status": status,
        "patient": patient,
        "targetDisease": TARGET,
        "immunizationEvent": event,
        "doseStatus": dose_status(),
        **extra,
    }


def full_body(patient_id: int, immunization_id: int, organization_id: int) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return evaluation_body(
        patient_id,
        immunization_id,
        resourceType="ImmunizationEvaluation",
        identifier=[
            {
                "system": EVALUATION_IDS,
                "value": "IE-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        date=DATE,
        authority={"reference": f"Organization/{organization_id}"},
        doseStatus=dose_status("valid", display="Valid"),
        doseStatusReason=[{"coding": [{"system": DOSE_REASON, "code": "agedoses"}]}, {"text": "Other"}],
        description="Evaluated against the seasonal flu schedule",
        series="Seasonal",
        doseNumberPositiveInt=1,
        seriesDosesPositiveInt=1,
    )


async def create_evaluation(client, body: dict) -> int:
    """Create an immunization evaluation and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
