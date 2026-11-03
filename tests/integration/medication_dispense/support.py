"""Shared helpers and payloads for MedicationDispense integration tests."""

BASE = "/api/fhir/v1/medication-dispenses"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_patient(client) -> int:
    """Create a minimal patient and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/patients/",
        json={"active": True, "name": [{"family": "Doe", "given": ["Jane"]}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_practitioner(client) -> int:
    """Create a minimal practitioner and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/practitioners/",
        json={"active": True},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_location(client) -> int:
    """Create a minimal location and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/locations/",
        json={"name": "Central Pharmacy", "status": "active"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_medication_dispense(patient_id: int) -> dict:
    return {
        "status": "completed",
        "medication_codeable_concept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "897122",
                    "display": "Amoxicillin 500 MG Oral Tablet",
                }
            ],
            "text": "Amoxicillin 500 MG Oral Tablet",
        },
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "quantity_value": 30.0,
        "quantity_unit": "TAB",
        "quantity_system": "http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
        "quantity_code": "TAB",
        "days_supply_value": 10.0,
        "days_supply_unit": "Day",
        "days_supply_system": "http://unitsofmeasure.org",
        "days_supply_code": "d",
        "when_prepared": "2026-01-15T10:00:00Z",
        "when_handed_over": "2026-01-15T11:00:00Z",
    }


def full_medication_dispense(
    patient_id: int,
    practitioner_id: int | None = None,
    location_id: int | None = None,
) -> dict:
    payload = {
        "status": "completed",
        "category": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
                    "code": "inpatient",
                    "display": "Inpatient",
                }
            ],
            "text": "Inpatient",
        },
        "medication_codeable_concept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "897122",
                    "display": "Amoxicillin 500 MG Oral Tablet",
                }
            ],
            "text": "Amoxicillin 500 MG Oral Tablet",
        },
        "subject": f"Patient/{patient_id}",
        "subject_display": "Jane Doe",
        "type": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
                    "code": "FF",
                    "display": "First Fill",
                }
            ],
            "text": "First Fill",
        },
        "quantity_value": 30.0,
        "quantity_unit": "TAB",
        "quantity_system": "http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
        "quantity_code": "TAB",
        "days_supply_value": 10.0,
        "days_supply_unit": "Day",
        "days_supply_system": "http://unitsofmeasure.org",
        "days_supply_code": "d",
        "when_prepared": "2026-01-15T10:00:00Z",
        "when_handed_over": "2026-01-15T11:00:00Z",
        "receiver": [{"reference": f"Patient/{patient_id}"}],
        "note": [
            {
                "text": "Patient advised to take with food.",
                "time": "2026-01-15T11:05:00Z",
                "author_string": "Pharmacist Dan",
            }
        ],
        "dosage_instruction": [
            {
                "text": "Take 1 tablet by mouth 3 times daily with meals",
                "additional_instruction": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "311504000",
                                "display": "With or after food",
                            }
                        ]
                    }
                ],
                "as_needed_boolean": False,
            }
        ],
        "substitution": {
            "was_substituted": True,
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-substanceAdminSubstitution",
                        "code": "G",
                        "display": "Generic Composition",
                    }
                ],
                "text": "Generic",
            },
            "reason": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActSubstanceAdminSubstitutionReason",
                            "code": "FP",
                            "display": "Formulary Policy",
                        }
                    ]
                }
            ],
        },
    }
    if practitioner_id:
        payload["performer"] = [
            {
                "actor": f"Practitioner/{practitioner_id}",
                "actor_display": "Dr. Bob",
                "function": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
                            "code": "packager",
                            "display": "Packager",
                        }
                    ],
                    "text": "Packager",
                },
            }
        ]
    if location_id:
        payload["location"] = f"Location/{location_id}"
        payload["destination"] = f"Location/{location_id}"

    return payload


async def create_medication_dispense(
    client, payload: dict, headers: dict | None = None
) -> dict:
    resp = await client.post(BASE + "/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()
