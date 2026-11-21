"""Shared helpers and payloads for diagnostic_report integration tests.

Request bodies are genuine FHIR R4 DiagnosticReport JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources a DiagnosticReport points at (and that point back at it) are created
# through their own routers.
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_location,
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)

BASE = "/api/fhir/v1/diagnostic-reports"
API = "/api/fhir/v1"

REPORT_IDS = "https://fhir-server.dev/fhir/identifier-system/report-id"
STATUS_SYSTEM = "http://hl7.org/fhir/diagnostic-report-status"
LOINC = "http://loinc.org"
SCT = "http://snomed.info/sct"
V2_0074 = "http://terminology.hl7.org/CodeSystem/v2-0074"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"

CODE = {
    "coding": [
        {
            "system": LOINC,
            "code": "58410-2",
            "display": "CBC panel - Blood by Automated count",
        }
    ]
}


def report_body(patient_id: int | None = None, status: str = "final", **extra) -> dict:
    """A valid minimal DiagnosticReport: R4 requires `status` and `code`. With no patient the
    subject is an absolute URL (not existence-checked)."""
    subject = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    return {"status": status, "code": CODE, "subject": subject, **extra}


def full_body(
    patient_id: int, encounter_id: int, practitioner_id: int, organization_id: int
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return report_body(
        patient_id,
        resourceType="DiagnosticReport",
        identifier=[
            {
                "system": REPORT_IDS,
                "value": "DR-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        basedOn=[{"reference": "ServiceRequest/80001"}],
        category=[
            {"coding": [{"system": V2_0074, "code": "LAB", "display": "Laboratory"}]}
        ],
        encounter={"reference": f"Encounter/{encounter_id}"},
        effectivePeriod={
            "start": "2023-01-15T09:30:00Z",
            "end": "2023-01-15T10:00:00Z",
        },
        issued="2023-01-15T12:00:00Z",
        performer=[
            {"reference": f"Practitioner/{practitioner_id}"},
            {"reference": f"Organization/{organization_id}"},
        ],
        resultsInterpreter=[{"reference": f"Practitioner/{practitioner_id}"}],
        specimen=[{"reference": "Specimen/310001"}],
        result=[{"reference": "Observation/160001"}],
        imagingStudy=[{"reference": "ImagingStudy/5"}],
        media=[{"comment": "Slide 1", "link": {"reference": "Media/9"}}],
        conclusion="Normal blood count.",
        conclusionCode=[
            {"coding": [{"system": SCT, "code": "17621005", "display": "Normal"}]}
        ],
        presentedForm=[
            {
                "contentType": "application/pdf",
                "url": "https://example.org/report.pdf",
                "title": "Report",
            }
        ],
    )


async def create_report(client, body: dict) -> int:
    """Create a diagnostic report and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
