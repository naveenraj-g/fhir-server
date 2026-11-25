"""Shared helpers and payloads for observation_definition integration tests.

Request bodies are genuine FHIR R4 ObservationDefinition JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

from tests.integration.practitioner_role.support import (
    create_organization,
)

BASE = "/api/fhir/v1/observation-definitions"
API = "/api/fhir/v1"

OBSERVATION_DEFINITION_IDS = (
    "https://fhir-server.dev/fhir/identifier-system/observation-definition-id"
)
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
OBS_CATEGORY = "http://terminology.hl7.org/CodeSystem/observation-category"


def observation_definition_body(code: str = "718-7", **extra) -> dict:
    """A valid minimal observation definition: R4 requires only `code`."""
    return {"code": {"coding": [{"system": LOINC, "code": code}]}, **extra}


def full_body(organization_id: int) -> dict:
    """Every element: none of them is indexed (R4 defines no search parameter), so all of it must
    round-trip through `content` unchanged."""
    return observation_definition_body(
        resourceType="ObservationDefinition",
        identifier=[
            {
                "system": OBSERVATION_DEFINITION_IDS,
                "value": "OD-1001",
                "type": {"coding": [{"system": V2_0203, "code": "ACSN"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        category=[
            {"coding": [{"system": OBS_CATEGORY, "code": "laboratory"}], "text": "Lab"}
        ],
        permittedDataType=["Quantity", "CodeableConcept", "string"],
        multipleResultsAllowed=False,
        method={"text": "automated count"},
        preferredReportName="Hemoglobin",
        quantitativeDetails={
            "customaryUnit": {"coding": [{"system": UCUM, "code": "g/dL"}]},
            "unit": {"coding": [{"system": UCUM, "code": "g/L"}]},
            "conversionFactor": 10.0,
            "decimalPrecision": 1,
        },
        qualifiedInterval=[
            {
                "category": "reference",
                "range": {
                    "low": {
                        "value": 12,
                        "unit": "g/dL",
                        "system": UCUM,
                        "code": "g/dL",
                    },
                    "high": {
                        "value": 16,
                        "unit": "g/dL",
                        "system": UCUM,
                        "code": "g/dL",
                    },
                },
                "context": {"text": "adult female"},
                "appliesTo": [{"text": "female"}],
                "gender": "female",
                "age": {
                    "low": {"value": 18, "unit": "a"},
                    "high": {"value": 65, "unit": "a"},
                },
                "gestationalAge": {"low": {"value": 0, "unit": "wk"}},
                "condition": "not pregnant",
            },
            {"category": "critical", "range": {"low": {"value": 7}}},
        ],
        validCodedValueSet={"reference": "ValueSet/valid"},
        normalCodedValueSet={"reference": "ValueSet/normal"},
        abnormalCodedValueSet={
            "reference": "https://example.org/fhir/ValueSet/abnormal"
        },
        criticalCodedValueSet={
            "identifier": {"system": "urn:vs", "value": "critical"},
            "display": "Critical values",
        },
    )


async def create_observation_definition(client, body: dict) -> int:
    """Create an observation definition and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
