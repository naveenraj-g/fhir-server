"""Shared helpers and payloads for immunization_recommendation integration tests.

Request bodies are genuine FHIR R4 ImmunizationRecommendation JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources an ImmunizationRecommendation points at (and that point back at it) are
# created through their own routers.
from tests.integration.condition.support import condition_body, create_condition  # noqa: F401
from tests.integration.immunization.support import (
    create_immunization,
    immunization_body,
)  # noqa: F401
from tests.integration.immunization_evaluation.support import (
    create_evaluation,
    evaluation_body,
)  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import create_organization  # noqa: F401

BASE = "/api/fhir/v1/immunization-recommendations"
API = "/api/fhir/v1"

RECOMMENDATION_IDS = (
    "https://fhir-server.dev/fhir/identifier-system/immunization-recommendation-id"
)
CVX = "http://hl7.org/fhir/sid/cvx"
SCT = "http://snomed.info/sct"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
STATUS = "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status"

DATE = "2023-01-15T09:30:00Z"


def status(code: str = "due", **extra) -> dict:
    return {"coding": [{"system": STATUS, "code": code, **extra}]}


def vaccine(code: str = "140", display: str | None = None) -> dict:
    return {
        "coding": [
            {"system": CVX, "code": code, **({"display": display} if display else {})}
        ]
    }


def entry(**extra) -> dict:
    """A valid recommendation entry: R4 requires `forecastStatus`, and `vaccineCode` or
    `targetDisease` (rule imr-1)."""
    return {"vaccineCode": [vaccine()], "forecastStatus": status(), **extra}


def recommendation_body(patient_id: int | None = None, **extra) -> dict:
    """A valid minimal ImmunizationRecommendation: R4 requires `patient`, `date` and a
    `recommendation`. With no patient the reference is an absolute URL (not existence-checked)."""
    patient = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    return {"patient": patient, "date": DATE, "recommendation": [entry()], **extra}


def full_body(
    patient_id: int,
    organization_id: int,
    immunization_id: int,
    condition_id: int,
    evaluation_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return recommendation_body(
        patient_id,
        resourceType="ImmunizationRecommendation",
        identifier=[
            {
                "system": RECOMMENDATION_IDS,
                "value": "IR-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        authority={"reference": f"Organization/{organization_id}"},
        recommendation=[
            {
                "vaccineCode": [vaccine("140", "Influenza vaccine")],
                "targetDisease": {
                    "coding": [
                        {"system": SCT, "code": "6142004", "display": "Influenza"}
                    ]
                },
                "contraindicatedVaccineCode": [vaccine("99")],
                "forecastStatus": status("due", display="Due"),
                "forecastReason": [{"text": "Seasonal"}],
                "dateCriterion": [
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "30980-7",
                                    "display": "Date vaccine due",
                                }
                            ]
                        },
                        "value": "2023-06-01T00:00:00Z",
                    }
                ],
                "description": "Seasonal flu shot",
                "series": "Seasonal",
                "doseNumberPositiveInt": 1,
                "seriesDosesPositiveInt": 1,
                "supportingImmunization": [
                    {"reference": f"Immunization/{immunization_id}"},
                    {"reference": f"ImmunizationEvaluation/{evaluation_id}"},
                ],
                "supportingPatientInformation": [
                    {"reference": f"Condition/{condition_id}"},
                    {"reference": "Observation/160001"},
                ],
            },
            {
                "vaccineCode": [vaccine("03", "MMR vaccine")],
                "forecastStatus": status("contraindicated"),
                "doseNumberString": "booster",
                "seriesDosesString": "many",
            },
        ],
    )


async def create_recommendation(client, body: dict) -> int:
    """Create an immunization recommendation and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
