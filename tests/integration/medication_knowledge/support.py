"""Shared helpers and payloads for MedicationKnowledge integration tests."""

BASE = "/api/fhir/v1/medication-knowledge"
ORG_BASE = "/api/fhir/v1/organizations"
MED_BASE = "/api/fhir/v1/medications"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_organization(client, name="Pharma Corp") -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        ORG_BASE + "/",
        json={"active": True, "name": name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def create_test_medication(client) -> int:
    """Create a minimal medication and return its public ID."""
    resp = await client.post(
        MED_BASE + "/",
        json={
            "status": "active",
            "code": {
                "text": "Amoxicillin 500mg capsule",
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "308182",
                        "display": "Amoxicillin 500 MG Oral Capsule",
                    }
                ],
            },
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def minimal_medication_knowledge() -> dict:
    return {
        "status": "active",
        "code": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "308182",
                    "display": "Amoxicillin 500 MG Oral Capsule",
                }
            ],
            "text": "Amoxicillin 500 MG Oral Capsule",
        },
    }


def full_medication_knowledge(
    org_id: int | None = None,
    assoc_med_id: int | None = None,
) -> dict:
    payload = {
        "status": "active",
        "code": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "308182",
                    "display": "Amoxicillin 500 MG Oral Capsule",
                }
            ],
            "text": "Amoxicillin 500 MG Oral Capsule",
        },
        "dose_form": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "385055001",
                    "display": "Oral Capsule",
                }
            ],
            "text": "Capsule",
        },
        "amount": {
            "value": 500.0,
            "unit": "mg",
            "system": "http://unitsofmeasure.org",
            "code": "mg",
        },
        "synonym": ["Amoxil", "Trimox"],
        "preparation_instruction": "Take with water before meals.",
        "packaging": {
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/medicationknowledge-package-type",
                        "code": "bot",
                        "display": "Bottle",
                    }
                ],
                "text": "Bottle",
            },
            "quantity": {
                "value": 100.0,
                "unit": "capsule",
            },
        },
        "product_type": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/medication-knowledge-product-type",
                        "code": "rx",
                        "display": "Prescription",
                    }
                ],
                "text": "Prescription Only",
            }
        ],
        "ingredient": [
            {
                "item_codeable_concept": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "27658006",
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
                        "unit": "capsule",
                        "system": "http://unitsofmeasure.org",
                        "code": "1",
                    },
                },
            }
        ],
        "intended_route": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "260548002",
                        "display": "Oral",
                    }
                ],
                "text": "Oral",
            }
        ],
        "cost": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/medication-knowledge-cost-type",
                            "code": "wholesale",
                            "display": "Wholesale Price",
                        }
                    ],
                    "text": "Wholesale",
                },
                "source": "Acme Supplies",
                "cost": {
                    "value": 15.50,
                    "currency": "USD",
                },
            }
        ],
        "monitoring_program": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/medication-knowledge-monitoring-program-type",
                            "code": "rems",
                            "display": "Risk Evaluation and Mitigation Strategy",
                        }
                    ],
                    "text": "REMS",
                },
                "name": "Safe Use Program",
            }
        ],
        "administration_guidelines": [
            {
                "indication_codeable_concept": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "87628006",
                            "display": "Bacterial infectious disease",
                        }
                    ],
                    "text": "Bacterial Infection",
                },
                "dosage": [
                    {
                        "type": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/dosage-type",
                                    "code": "adult",
                                    "display": "Adult",
                                }
                            ],
                            "text": "Adult standard dose",
                        },
                        "dosage": [{"text": "500 mg every 8 hours"}],
                    }
                ],
                "patient_characteristics": [
                    {
                        "characteristic_codeable_concept": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "424144002",
                                    "display": "Age group",
                                }
                            ],
                            "text": "Age Group",
                        },
                        "value": ["Adult"],
                    }
                ],
            }
        ],
        "medicine_classification": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/medicine-classification-type",
                            "code": "atc",
                            "display": "Anatomical Therapeutic Chemical",
                        }
                    ],
                    "text": "ATC",
                },
                "classification": [
                    {
                        "coding": [
                            {
                                "system": "http://www.whocc.no/atc",
                                "code": "J01CA04",
                                "display": "amoxicillin",
                            }
                        ],
                        "text": "Beta-lactamase sensitive penicillins",
                    }
                ],
            }
        ],
        "drug_characteristic": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/medicationknowledge-characteristic",
                            "code": "color",
                            "display": "Color",
                        }
                    ],
                    "text": "Color",
                },
                "value_string": "Yellow / Maroon",
            }
        ],
    }
    if org_id is not None:
        payload["manufacturer"] = f"Organization/{org_id}"
        payload["manufacturer_display"] = "Pharma Corp"
        payload["regulatory"] = [
            {
                "regulatory_authority": f"Organization/{org_id}",
                "regulatory_authority_display": "Pharma Corp",
                "substitution": [
                    {
                        "type": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/medicationknowledge-substitution",
                                    "code": "generic",
                                    "display": "Generic Substitution",
                                }
                            ],
                            "text": "Generic",
                        },
                        "allowed": True,
                    }
                ],
                "schedule": [
                    {
                        "schedule": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/medication-schedule",
                                    "code": "schedule4",
                                    "display": "Schedule IV",
                                }
                            ],
                            "text": "Schedule IV",
                        }
                    }
                ],
                "max_dispense": {
                    "quantity": {
                        "value": 30.0,
                        "unit": "capsule",
                    },
                    "period": {
                        "value": 30.0,
                        "unit": "days",
                        "system": "http://unitsofmeasure.org",
                        "code": "d",
                    },
                },
            }
        ]
    if assoc_med_id is not None:
        payload["associated_medication"] = [f"Medication/{assoc_med_id}"]
    return payload


async def create_medication_knowledge(client, **overrides) -> dict:
    payload = minimal_medication_knowledge()
    payload.update(overrides)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
