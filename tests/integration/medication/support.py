"""Shared helpers and payloads for medication integration tests.

Request bodies are genuine FHIR R4 Medication JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

from tests.integration.practitioner_role.support import create_organization

BASE = "/api/fhir/v1/medications"
API = "/api/fhir/v1"

MED_IDS = "https://fhir-server.dev/fhir/identifier-system/medication-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SCT = "http://snomed.info/sct"


def concept(system: str, code: str, display: str | None = None) -> dict:
    return {
        "coding": [
            {
                "system": system,
                "code": code,
                **({"display": display} if display else {}),
            }
        ]
    }


def medication_body(**extra) -> dict:
    """A valid minimal Medication (every R4 element is optional)."""
    return dict(extra)


def full_body(organization_id: int, ingredient_id: int) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return medication_body(
        resourceType="Medication",
        identifier=[
            {
                "system": MED_IDS,
                "value": "MED-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        code=concept(RXNORM, "1049502", "Oxycodone 10 MG ER tablet"),
        status="active",
        manufacturer={"reference": f"Organization/{organization_id}"},
        form=concept(SCT, "385057009", "Film-coated tablet"),
        amount={
            "numerator": {"value": 30, "unit": "tablet"},
            "denominator": {"value": 1, "unit": "package"},
        },
        ingredient=[
            {
                "itemCodeableConcept": concept(RXNORM, "7804", "Oxycodone"),
                "isActive": True,
                "strength": {
                    "numerator": {"value": 10, "unit": "mg"},
                    "denominator": {"value": 1, "unit": "tablet"},
                },
            },
            {
                "itemReference": {"reference": f"Medication/{ingredient_id}"},
                "isActive": False,
            },
        ],
        batch={"lotNumber": "LOT-1", "expirationDate": "2027-06-30"},
    )


async def create_medication(client, body: dict) -> int:
    """Create a medication and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
