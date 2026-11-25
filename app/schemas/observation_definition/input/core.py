"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.observation_definition import (
    ObservationDefinition,
    ObservationDefinitionPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "ObservationDefinition",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/observation-definition-id",
            "value": "OD-1",
        }
    ],
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                }
            ]
        }
    ],
    "code": {"coding": [{"system": "http://loinc.org", "code": "718-7"}]},
    "permittedDataType": ["Quantity"],
    "multipleResultsAllowed": False,
    "preferredReportName": "Hemoglobin",
    "quantitativeDetails": {
        "unit": {"coding": [{"system": "http://unitsofmeasure.org", "code": "g/dL"}]},
        "decimalPrecision": 1,
    },
    "qualifiedInterval": [
        {
            "category": "reference",
            "range": {
                "low": {"value": 12, "unit": "g/dL"},
                "high": {"value": 16, "unit": "g/dL"},
            },
            "gender": "female",
        }
    ],
}

_PATCH_EXAMPLE = {"preferredReportName": "Haemoglobin", "multipleResultsAllowed": True}


class ObservationDefinitionCreateSchema(ObservationDefinition):
    "POST body - a FHIR R4 ObservationDefinition resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ObservationDefinitionPatchSchema(ObservationDefinitionPatch):
    "PATCH body - a partial FHIR R4 ObservationDefinition (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
