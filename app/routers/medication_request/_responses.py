from app.core.schema_utils import inline_schema
from app.schemas.medication_request import (
    FHIRMedicationRequestBundle,
    FHIRMedicationRequestSchema,
    PaginatedMedicationRequestResponse,
    PlainMedicationRequestResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "MedicationRequest not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainMedicationRequestResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRMedicationRequestSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of medication requests",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedMedicationRequestResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRMedicationRequestBundle.model_json_schema())},
        },
    }
}
