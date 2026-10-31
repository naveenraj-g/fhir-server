"""Shared helpers and payloads for observation_definition integration tests."""

BASE = "/api/fhir/v1/observation-definitions"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def minimal_observation_definition() -> dict:
    return {
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "15074-8",
                    "display": "Glucose [Moles/volume] in Blood",
                }
            ],
            "text": "Glucose in Blood",
        }
    }


def full_observation_definition() -> dict:
    return {
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "15074-8",
                    "display": "Glucose [Moles/volume] in Blood",
                }
            ],
            "text": "Glucose in Blood",
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory",
                    }
                ],
                "text": "Laboratory",
            }
        ],
        "permitted_data_type": ["Quantity", "string"],
        "multiple_results_allowed": False,
        "method": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "271077007",
                    "display": "Blood glucose measurement",
                }
            ],
            "text": "Test strip reflectance",
        },
        "preferred_report_name": "Blood Glucose",
        "quantitative_details": {
            "customary_unit": {
                "coding": [
                    {
                        "system": "http://unitsofmeasure.org",
                        "code": "mg/dL",
                        "display": "mg/dL",
                    }
                ],
                "text": "mg/dL",
            },
            "unit": {
                "coding": [
                    {
                        "system": "http://unitsofmeasure.org",
                        "code": "mmol/L",
                        "display": "mmol/L",
                    }
                ],
                "text": "mmol/L",
            },
            "conversion_factor": 0.0555,
            "decimal_precision": 1,
        },
        "qualified_interval": [
            {
                "category": "reference",
                "range_low_value": 70.0,
                "range_low_unit": "mg/dL",
                "range_high_value": 99.0,
                "range_high_unit": "mg/dL",
                "gender": "male",
                "condition": "Fasting blood sugar",
            }
        ],
        "valid_coded_value_set": "ValueSet/40001",
        "normal_coded_value_set": "ValueSet/40002",
        "abnormal_coded_value_set": "ValueSet/40003",
        "critical_coded_value_set": "ValueSet/40004",
        "identifier": [
            {
                "use": "official",
                "system": "http://example.org/obsdef",
                "value": "OBSDEF-12345",
            }
        ],
    }


async def create_observation_definition(client, **overrides) -> dict:
    """Helper to create an ObservationDefinition and return the response json."""
    payload = minimal_observation_definition()
    payload.update(overrides)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
