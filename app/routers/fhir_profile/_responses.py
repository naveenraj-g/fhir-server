from app.core.schema_utils import inline_schema
from app.schemas.fhir_profile import FhirProfileListResponse, FhirProfileResponse

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(FhirProfileResponse.model_json_schema())
            }
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(FhirProfileListResponse.model_json_schema())
            }
        }
    }
}
