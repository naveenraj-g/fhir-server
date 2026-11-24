"""Shared helpers and payloads for risk_assessment integration tests.

Request bodies are genuine FHIR R4 RiskAssessment JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

# The resources a RiskAssessment points at (and that point back at it) are created through
# their own routers.
from tests.integration.condition.support import condition_body, create_condition  # noqa: F401
from tests.integration.diagnostic_report.support import create_report, report_body  # noqa: F401
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)

BASE = "/api/fhir/v1/risk-assessments"
API = "/api/fhir/v1"

ASSESSMENT_IDS = "https://fhir-server.dev/fhir/identifier-system/risk-assessment-id"
SCT = "http://snomed.info/sct"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
RISK = "http://terminology.hl7.org/CodeSystem/risk-probability"
UCUM = "http://unitsofmeasure.org"


def risk(code: str = "moderate", display: str | None = None) -> dict:
    return {
        "coding": [
            {"system": RISK, "code": code, **({"display": display} if display else {})}
        ]
    }


def percent(value: float | int) -> dict:
    return {"value": value, "unit": "%", "system": UCUM, "code": "%"}


def assessment_body(
    patient_id: int | None = None, status: str = "final", **extra
) -> dict:
    """A valid minimal RiskAssessment: R4 requires `status` and `subject`. With no patient the
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
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return assessment_body(
        patient_id,
        resourceType="RiskAssessment",
        identifier=[
            {
                "system": ASSESSMENT_IDS,
                "value": "RA-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        basedOn={"reference": "ServiceRequest/80001"},
        parent={"reference": "Device/580001"},
        method={
            "coding": [
                {"system": SCT, "code": "225338004", "display": "Risk assessment"}
            ]
        },
        code={
            "coding": [
                {
                    "system": SCT,
                    "code": "709510001",
                    "display": "Assessment of risk for cardiovascular disease",
                }
            ]
        },
        encounter={"reference": f"Encounter/{encounter_id}"},
        occurrenceDateTime="2023-01-15T09:30:00Z",
        condition={"reference": f"Condition/{condition_id}"},
        performer={"reference": f"Practitioner/{practitioner_id}"},
        reasonCode=[{"text": "Family history of heart disease"}],
        reasonReference=[
            {"reference": f"Condition/{condition_id}"},
            {"reference": "Observation/160001"},
        ],
        basis=[{"reference": "Observation/160002"}],
        prediction=[
            {
                "outcome": {
                    "coding": [
                        {
                            "system": SCT,
                            "code": "54329005",
                            "display": "Acute myocardial infarction",
                        }
                    ]
                },
                "probabilityDecimal": 12.5,
                "qualitativeRisk": risk("moderate", "moderate likelihood"),
                "relativeRisk": 1.4,
                "whenRange": {
                    "low": {"value": 40, "unit": "yr", "system": UCUM, "code": "a"},
                    "high": {"value": 50, "unit": "yr", "system": UCUM, "code": "a"},
                },
                "rationale": "Based on lipid panel and blood pressure.",
            },
            {
                "outcome": {"text": "Stroke"},
                "probabilityRange": {"low": percent(5), "high": percent(10)},
                "qualitativeRisk": risk("low"),
                "whenPeriod": {"start": "2023-01-01", "end": "2033-01-01"},
            },
        ],
        mitigation="Statin therapy and lifestyle changes.",
        note=[
            {
                "text": "Reassess in 12 months.",
                "time": "2023-01-15T10:00:00Z",
                "authorString": "Nurse Joy",
            }
        ],
    )


async def create_assessment(client, body: dict) -> int:
    """Create a risk assessment and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
