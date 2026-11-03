from app.core.schema_utils import inline_schema
from app.schemas.medication_dispense import (
    FHIRMedicationDispenseBundle,
    FHIRMedicationDispenseSchema,
    PaginatedMedicationDispenseResponse,
    PlainMedicationDispenseResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "MedicationDispense not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PlainMedicationDispenseResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRMedicationDispenseSchema.model_json_schema()
                )
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of medication dispenses",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PaginatedMedicationDispenseResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRMedicationDispenseBundle.model_json_schema()
                )
            },
        },
    }
}
