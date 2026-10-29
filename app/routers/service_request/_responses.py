from app.core.schema_utils import inline_schema
from app.schemas.service_request import (
    FHIRServiceRequestBundle,
    FHIRServiceRequestSchema,
    PaginatedServiceRequestResponse,
    PlainServiceRequestResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "ServiceRequest not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainServiceRequestResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRServiceRequestSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of service requests",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedServiceRequestResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRServiceRequestBundle.model_json_schema())},
        },
    }
}
