"""Shared helpers and payloads for immunization integration tests.

Request bodies are genuine FHIR R4 Immunization JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources an Immunization points at (and that point back at it) are created
# through their own routers.
from tests.integration.condition.support import condition_body, create_condition  # noqa: F401
from tests.integration.diagnostic_report.support import create_report, report_body  # noqa: F401
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_location,
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)

BASE = "/api/fhir/v1/immunizations"
API = "/api/fhir/v1"

IMMUNIZATION_IDS = "https://fhir-server.dev/fhir/identifier-system/immunization-id"
STATUS_SYSTEM = "http://hl7.org/fhir/event-status"
CVX = "http://hl7.org/fhir/sid/cvx"
SCT = "http://snomed.info/sct"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
ACT_REASON = "http://terminology.hl7.org/CodeSystem/v3-ActReason"

VACCINE = {
    "coding": [
        {
            "system": CVX,
            "code": "140",
            "display": "Influenza, seasonal, injectable, preservative free",
        }
    ]
}


def immunization_body(
    patient_id: int | None = None, status: str = "completed", **extra
) -> dict:
    """A valid minimal Immunization: R4 requires `status`, `vaccineCode`, `patient` and
    `occurrence[x]`. With no patient the reference is an absolute URL (not existence-checked)."""
    patient = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    body = {"status": status, "vaccineCode": VACCINE, "patient": patient}
    if "occurrenceString" not in extra:
        body.setdefault("occurrenceDateTime", "2023-01-15T09:30:00Z")
    return {**body, **extra}


def full_body(
    patient_id: int,
    encounter_id: int,
    practitioner_id: int,
    organization_id: int,
    location_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return immunization_body(
        patient_id,
        resourceType="Immunization",
        identifier=[
            {
                "system": IMMUNIZATION_IDS,
                "value": "IM-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        statusReason={
            "coding": [{"system": ACT_REASON, "code": "PATOBJ"}],
            "text": "Patient objection",
        },
        encounter={"reference": f"Encounter/{encounter_id}"},
        recorded="2023-01-15T10:00:00Z",
        primarySource=True,
        reportOrigin={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-origin",
                    "code": "provider",
                }
            ]
        },
        location={"reference": f"Location/{location_id}"},
        manufacturer={"reference": f"Organization/{organization_id}"},
        lotNumber="AAJN11K",
        expirationDate="2025-02-15",
        site={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                    "code": "LA",
                    "display": "left arm",
                }
            ]
        },
        route={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
                    "code": "IM",
                }
            ]
        },
        doseQuantity={"value": 5, "system": "http://unitsofmeasure.org", "code": "mg"},
        performer=[
            {
                "function": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
                            "code": "AP",
                        }
                    ]
                },
                "actor": {"reference": f"Practitioner/{practitioner_id}"},
            },
            {"actor": {"reference": f"Organization/{organization_id}"}},
        ],
        note=[
            {
                "text": "Given in the left arm",
                "time": "2023-01-15T10:05:00Z",
                "authorString": "Nurse Joy",
            }
        ],
        reasonCode=[
            {
                "coding": [
                    {
                        "system": SCT,
                        "code": "429060002",
                        "display": "Procedure to meet occupational requirement",
                    }
                ]
            }
        ],
        reasonReference=[{"reference": "Observation/160001"}],
        isSubpotent=False,
        subpotentReason=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-subpotent-reason",
                        "code": "partial",
                    }
                ]
            }
        ],
        education=[
            {
                "documentType": "flu-fact-sheet",
                "reference": "https://example.org/flu",
                "publicationDate": "2022-10-01",
            },
        ],
        programEligibility=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-program-eligibility",
                        "code": "ineligible",
                    }
                ]
            }
        ],
        fundingSource={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-funding-source",
                    "code": "private",
                }
            ]
        },
        reaction=[
            {
                "date": "2023-01-16T08:00:00Z",
                "detail": {"reference": "Observation/160002"},
                "reported": True,
            }
        ],
        protocolApplied=[
            {
                "series": "2-dose",
                "authority": {"reference": f"Organization/{organization_id}"},
                "targetDisease": [
                    {
                        "coding": [
                            {"system": SCT, "code": "6142004", "display": "Influenza"}
                        ]
                    }
                ],
                "doseNumberPositiveInt": 1,
                "seriesDosesPositiveInt": 2,
            }
        ],
    )


async def create_immunization(client, body: dict) -> int:
    """Create an immunization and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
