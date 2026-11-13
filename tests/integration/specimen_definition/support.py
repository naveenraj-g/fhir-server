"""Shared helpers and payloads for SpecimenDefinition integration tests."""

BASE = "/api/fhir/v1/specimen-definitions"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


async def create_test_organization(client) -> int:
    """Create a minimal organization and return its public ID."""
    resp = await client.post(
        "/api/fhir/v1/organizations/",
        json={"active": True, "name": "Acme Pathology Lab"},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


def minimal_specimen_definition() -> dict:
    return {
        "time_aspect": "fasting",
    }


async def create_specimen_definition(client) -> int:
    """Create a minimal specimen definition and return its public ID."""
    resp = await client.post(
        f"{BASE}/",
        json=minimal_specimen_definition(),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def full_specimen_definition(organization_id: int | None = None) -> dict:
    payload = {
        "identifier": {
            "use": "official",
            "system": "http://example.org/specimen-definitions",
            "value": "SERUM-2026-001",
            "type_text": "Specimen Code",
            "type_coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "FILL",
                    "display": "Filler Identifier",
                }
            ],
            "period_start": "2026-02-01T10:00:00Z",
            "period_end": "2026-02-01T10:00:00Z",
        },
        "type_collected": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "122555007",
                    "display": "Venous blood specimen",
                }
            ],
            "text": "Venous blood",
        },
        "patient_preparation": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "726054005",
                        "display": "Fasting",
                    }
                ],
                "text": "12 hour fasting prior to collection",
            }
        ],
        "time_aspect": "morning",
        "collection": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "28520004",
                        "display": "Venipuncture",
                    }
                ],
                "text": "Venipuncture procedure",
            }
        ],
        "type_tested": [
            {
                "is_derived": True,
                "type": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "119364003",
                            "display": "Serum specimen",
                        }
                    ],
                    "text": "Serum",
                },
                "preference": "preferred",
                "requirement": "Fasting sample preferred",
                "retention_time_value": 24.0,
                "retention_time_comparator": "<=",
                "retention_time_unit": "h",
                "retention_time_system": "http://unitsofmeasure.org",
                "retention_time_code": "h",
                "container": {
                    "material": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "61088005",
                                "display": "Plastic",
                            }
                        ],
                        "text": "Plastic",
                    },
                    "type": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "706053007",
                                "display": "General specimen container",
                            }
                        ],
                        "text": "Vacuum blood collection tube",
                    },
                    "cap": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/container-cap",
                                "code": "red",
                                "display": "Red Cap",
                            }
                        ],
                        "text": "Red top",
                    },
                    "description": "Serum separator tube (SST)",
                    "capacity_value": 5.0,
                    "capacity_unit": "mL",
                    "capacity_system": "http://unitsofmeasure.org",
                    "capacity_code": "mL",
                    "minimum_volume_quantity_value": 1.0,
                    "minimum_volume_quantity_unit": "mL",
                    "minimum_volume_quantity_system": "http://unitsofmeasure.org",
                    "minimum_volume_quantity_code": "mL",
                    "additive": [
                        {
                            "additive_codeable_concept": {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": "88480006",
                                        "display": "Lithium heparin",
                                    }
                                ],
                                "text": "Heparin",
                            },
                            "additive_reference": {
                                "reference": "Substance/10001",
                                "display": "Lithium Heparin",
                            },
                        }
                    ],
                    "preparation": "Invert gently 5 times",
                },
                "rejection_criterion": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/rejection-criteria",
                                "code": "hemolyzed",
                                "display": "Hemolyzed specimen",
                            }
                        ],
                        "text": "Grossly hemolyzed",
                    }
                ],
                "handling": [
                    {
                        "temperature_qualifier": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/handling-condition",
                                    "code": "refrigerated",
                                    "display": "Refrigerated",
                                }
                            ],
                            "text": "Refrigerated temperature",
                        },
                        "temperature_range_low_value": 2.0,
                        "temperature_range_low_unit": "degC",
                        "temperature_range_low_system": "http://unitsofmeasure.org",
                        "temperature_range_low_code": "Cel",
                        "temperature_range_high_value": 8.0,
                        "temperature_range_high_unit": "degC",
                        "temperature_range_high_system": "http://unitsofmeasure.org",
                        "temperature_range_high_code": "Cel",
                        "max_duration_value": 48.0,
                        "max_duration_comparator": "<=",
                        "max_duration_unit": "h",
                        "max_duration_system": "http://unitsofmeasure.org",
                        "max_duration_code": "h",
                        "instruction": "Store at 2-8 degC until analysis.",
                    }
                ],
            }
        ],
    }
    if organization_id:
        payload["identifier"]["assigner"] = f"Organization/{organization_id}"
        payload["identifier"]["assigner_display"] = "Acme Pathology Lab"
    return payload
