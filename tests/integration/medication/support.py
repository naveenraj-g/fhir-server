"""Shared helpers and payloads for Medication integration tests."""

BASE = "/api/fhir/v1/medications"
ORG_BASE = "/api/fhir/v1/organizations"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_organization(client, name="Acme Pharmaceuticals") -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        ORG_BASE + "/",
        json={"active": True, "name": name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_medication() -> dict:
    return {
        "status": "active",
        "code": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "897122",
                    "display": "Amoxicillin 500 MG Oral Tablet",
                }
            ],
            "text": "Amoxicillin 500 MG Oral Tablet",
        },
    }


def full_medication(
    org_id: int | None = None,
    ingredient_med_id: int | None = None,
) -> dict:
    payload = {
        "status": "active",
        "identifier": [
            {
                "system": "http://example.org/medications",
                "value": "MED-12345",
                "use": "official",
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "897122",
                    "display": "Amoxicillin 500 MG Oral Tablet",
                }
            ],
            "text": "Amoxicillin 500 MG Oral Tablet",
        },
        "form": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "385055001",
                    "display": "Tablet dose form",
                }
            ],
            "text": "Tablet",
        },
        "amount": {
            "numerator": {
                "value": 1.0,
                "unit": "TAB",
                "system": "http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
                "code": "TAB",
            },
            "denominator": {
                "value": 1.0,
                "unit": "package",
            },
        },
        "ingredient": [
            {
                "item_codeable_concept": {
                    "coding": [
                        {
                            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                            "code": "70618",
                            "display": "Amoxicillin",
                        }
                    ],
                    "text": "Amoxicillin",
                },
                "is_active": True,
                "strength": {
                    "numerator": {
                        "value": 500.0,
                        "unit": "mg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mg",
                    },
                    "denominator": {
                        "value": 1.0,
                        "unit": "TAB",
                        "system": "http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
                        "code": "TAB",
                    },
                },
            }
        ],
        "batch": {
            "lot_number": "LOT-9876",
            "expiration_date": "2027-12-31T00:00:00Z",
        },
    }
    if org_id is not None:
        payload["manufacturer"] = f"Organization/{org_id}"
        payload["manufacturer_display"] = "Acme Pharmaceuticals"
    if ingredient_med_id is not None:
        payload["ingredient"].append(
            {
                "item_reference": f"Medication/{ingredient_med_id}",
                "item_display": "Clavulanate Potassium",
                "is_active": True,
                "strength": {
                    "numerator": {
                        "value": 125.0,
                        "unit": "mg",
                    },
                    "denominator": {
                        "value": 1.0,
                        "unit": "TAB",
                    },
                },
            }
        )
    return payload


async def create_medication(client, payload: dict | None = None) -> dict:
    if payload is None:
        payload = minimal_medication()
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
