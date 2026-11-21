"""Shared helpers and payloads for detected_issue integration tests.

Request bodies are genuine FHIR R4 DetectedIssue JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

# The resources a DetectedIssue points at (and that point back at it) are created through
# their own routers.
from tests.integration.allergy_intolerance.support import (
    allergy_body,
    create_allergy_intolerance,
)  # noqa: F401
from tests.integration.clinical_impression.support import (
    create_impression,
    impression_body,
)  # noqa: F401
from tests.integration.condition.support import condition_body, create_condition  # noqa: F401
from tests.integration.diagnostic_report.support import create_report, report_body  # noqa: F401
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)

BASE = "/api/fhir/v1/detected-issues"
API = "/api/fhir/v1"

ISSUE_IDS = "https://fhir-server.dev/fhir/identifier-system/detected-issue-id"
ACT_CODE = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"


def category(code: str = "DUPTHPY", display: str | None = None) -> dict:
    return {
        "coding": [
            {
                "system": ACT_CODE,
                "code": code,
                **({"display": display} if display else {}),
            }
        ]
    }


def issue_body(patient_id: int | None = None, status: str = "final", **extra) -> dict:
    """A valid minimal DetectedIssue: R4 requires `status`. With no patient the `patient` element is
    omitted."""
    body = {"status": status, **extra}
    if patient_id:
        body["patient"] = {"reference": f"Patient/{patient_id}"}
    return body


def full_body(
    patient_id: int,
    practitioner_id: int,
    condition_id: int,
    report_id: int,
    organization_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return issue_body(
        patient_id,
        resourceType="DetectedIssue",
        identifier=[
            {
                "system": ISSUE_IDS,
                "value": "DI-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        code=category("DUPTHPY", "Duplicate therapy alert"),
        severity="high",
        identifiedDateTime="2023-01-15T09:30:00Z",
        author={"reference": f"Practitioner/{practitioner_id}"},
        implicated=[
            {"reference": f"Condition/{condition_id}"},
            {"reference": "MedicationRequest/90001"},
        ],
        evidence=[
            {
                "code": [{"text": "Two active statin prescriptions"}],
                "detail": [{"reference": f"DiagnosticReport/{report_id}"}],
            }
        ],
        detail="The patient is prescribed two drugs of the same class.",
        reference="http://example.org/protocols/duplicate-therapy",
        mitigation=[
            {
                "action": {"text": "Stopped the older prescription"},
                "date": "2023-01-16T08:00:00Z",
                "author": {"reference": f"Practitioner/{practitioner_id}"},
            }
        ],
    )


async def create_issue(client, body: dict) -> int:
    """Create a detected issue and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
