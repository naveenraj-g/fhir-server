from app.core.schema_utils import inline_schema
from app.schemas.medication_statement import (
    FHIRMedicationStatementBundle,
    FHIRMedicationStatementSchema,
    PaginatedMedicationStatementResponse,
    PlainMedicationStatementResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "MedicationStatement not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PlainMedicationStatementResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRMedicationStatementSchema.model_json_schema()
                )
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of medication statements",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PaginatedMedicationStatementResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRMedicationStatementBundle.model_json_schema()
                )
            },
        },
    }
}
