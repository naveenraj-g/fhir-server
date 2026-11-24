"""Shared helpers and payloads for specimen_definition integration tests.

Request bodies are genuine FHIR R4 SpecimenDefinition JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
)

BASE = "/api/fhir/v1/specimen-definitions"
API = "/api/fhir/v1"

SPECIMEN_DEFINITION_IDS = (
    "https://fhir-server.dev/fhir/identifier-system/specimen-definition-id"
)
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
V2_0487 = "http://terminology.hl7.org/CodeSystem/v2-0487"
UCUM = "http://unitsofmeasure.org"


def concept(code: str, display: str | None = None, system: str = V2_0487) -> dict:
    return {
        "coding": [
            {
                "system": system,
                "code": code,
                **({"display": display} if display else {}),
            }
        ]
    }


def specimen_definition_body(**extra) -> dict:
    """A valid minimal specimen definition: R4 has no required top-level element."""
    return {"typeCollected": concept("BLD"), **extra}


def type_tested(container_type: str | None = None, **extra) -> dict:
    """One typeTested entry (R4 requires its `preference`)."""
    entry = {"preference": "preferred", **extra}
    if container_type:
        entry["container"] = {"type": concept(container_type)}
    return entry


def full_body(organization_id: int) -> dict:
    """Every element, including the ones no search parameter reads (they must round-trip)."""
    return specimen_definition_body(
        resourceType="SpecimenDefinition",
        identifier={
            "system": SPECIMEN_DEFINITION_IDS,
            "value": "SD-1001",
            "type": {"coding": [{"system": V2_0203, "code": "ACSN"}]},
            "assigner": {"reference": f"Organization/{organization_id}"},
        },
        typeCollected=concept("BLD", "Whole blood"),
        patientPreparation=[{"text": "Fasting for 8 hours"}, concept("FAST")],
        timeAspect="Morning",
        collection=[{"text": "Venipuncture"}],
        typeTested=[
            {
                "isDerived": False,
                "type": {"text": "Whole blood"},
                "preference": "preferred",
                "container": {
                    "material": {"text": "glass"},
                    "type": concept("SPECIMEN", "Specimen"),
                    "cap": {"text": "purple"},
                    "description": "EDTA tube",
                    "capacity": {
                        "value": 5,
                        "unit": "mL",
                        "system": UCUM,
                        "code": "mL",
                    },
                    "minimumVolumeQuantity": {"value": 1, "unit": "mL"},
                    "additive": [
                        {"additiveCodeableConcept": {"text": "EDTA"}},
                        {"additiveReference": {"reference": "Substance/1"}},
                    ],
                    "preparation": "Mix gently",
                },
                "requirement": "Keep cold",
                "retentionTime": {"value": 7, "unit": "d", "system": UCUM, "code": "d"},
                "rejectionCriterion": [{"text": "hemolyzed"}],
                "handling": [
                    {
                        "temperatureQualifier": {"text": "refrigerated"},
                        "temperatureRange": {
                            "low": {"value": 2, "unit": "Cel"},
                            "high": {"value": 8, "unit": "Cel"},
                        },
                        "maxDuration": {"value": 24, "unit": "h"},
                        "instruction": "Do not freeze",
                    }
                ],
            },
            {
                "preference": "alternate",
                "container": {
                    "type": concept("TUBE", "Tube"),
                    "minimumVolumeString": "about 1 mL",
                },
            },
        ],
    )


async def create_specimen_definition(client, body: dict) -> int:
    """Create a specimen definition and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
