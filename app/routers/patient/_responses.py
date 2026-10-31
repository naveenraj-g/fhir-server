from app.core.schema_utils import inline_schema
from app.schemas.patient import (
    FHIRPatientBundle,
    FHIRPatientSchema,
    PaginatedPatientResponse,
    PlainPatientResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "Patient not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(PlainPatientResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRPatientSchema.model_json_schema())
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of patients",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PaginatedPatientResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRPatientBundle.model_json_schema())
            },
        },
    }
}
