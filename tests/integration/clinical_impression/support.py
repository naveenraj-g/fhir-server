"""Shared helpers and payloads for clinical_impression integration tests.

Request bodies are genuine FHIR R4 ClinicalImpression JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

# The resources a ClinicalImpression points at (and that point back at it) are created through
# their own routers.
from tests.integration.allergy_intolerance.support import (
    allergy_body,
    create_allergy_intolerance,
)  # noqa: F401
from tests.integration.condition.support import condition_body, create_condition  # noqa: F401
from tests.integration.diagnostic_report.support import create_report, report_body  # noqa: F401
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.family_member_history.support import create_history, history_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.risk_assessment.support import assessment_body as risk_body  # noqa: F401
from tests.integration.risk_assessment.support import create_assessment as create_risk  # noqa: F401

BASE = "/api/fhir/v1/clinical-impressions"
API = "/api/fhir/v1"

IMPRESSION_IDS = "https://fhir-server.dev/fhir/identifier-system/clinical-impression-id"
SCT = "http://snomed.info/sct"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"


def finding(code: str, display: str | None = None, **extra) -> dict:
    """A finding with a coded `itemCodeableConcept`."""
    return {
        "itemCodeableConcept": {
            "coding": [
                {
                    "system": SCT,
                    "code": code,
                    **({"display": display} if display else {}),
                }
            ]
        },
        **extra,
    }


def impression_body(
    patient_id: int | None = None, status: str = "completed", **extra
) -> dict:
    """A valid minimal ClinicalImpression: R4 requires `status` and `subject`. With no patient the
    subject is an absolute URL (not existence-checked)."""
    subject = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    return {"status": status, "subject": subject, **extra}


def full_body(
    patient_id: int,
    encounter_id: int,
    condition_id: int,
    practitioner_id: int,
    organization_id: int,
    report_id: int,
    risk_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return impression_body(
        patient_id,
        resourceType="ClinicalImpression",
        identifier=[
            {
                "system": IMPRESSION_IDS,
                "value": "CI-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        statusReason={"text": "Completed after review"},
        code={
            "coding": [
                {"system": SCT, "code": "225338004", "display": "Risk assessment"}
            ],
            "text": "Assessment",
        },
        description="Assessment of the patient's chest pain.",
        encounter={"reference": f"Encounter/{encounter_id}"},
        effectiveDateTime="2023-01-15T09:30:00Z",
        date="2023-01-15T10:00:00Z",
        assessor={"reference": f"Practitioner/{practitioner_id}"},
        problem=[{"reference": f"Condition/{condition_id}"}],
        investigation=[
            {
                "code": {"text": "Initial examination"},
                "item": [
                    {"reference": f"DiagnosticReport/{report_id}"},
                    {"reference": "Observation/160001"},
                ],
            }
        ],
        protocol=["http://example.org/protocols/chest-pain"],
        summary="Stable angina suspected; stress test arranged.",
        finding=[
            finding("194828000", "Angina", basis="Exercise ECG and history."),
            {"itemReference": {"reference": f"Condition/{condition_id}"}},
        ],
        prognosisCodeableConcept=[{"text": "Good"}],
        prognosisReference=[{"reference": f"RiskAssessment/{risk_id}"}],
        supportingInfo=[{"reference": "Observation/160002"}],
        note=[
            {
                "text": "Review in 2 weeks.",
                "time": "2023-01-15T10:30:00Z",
                "authorString": "Nurse Joy",
            }
        ],
    )


async def create_impression(client, body: dict) -> int:
    """Create a clinical impression and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
