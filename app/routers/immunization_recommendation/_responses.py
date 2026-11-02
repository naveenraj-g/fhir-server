from app.core.schema_utils import inline_schema
from app.schemas.immunization_recommendation import (
    FHIRImmunizationRecommendationBundle,
    FHIRImmunizationRecommendationSchema,
    PaginatedImmunizationRecommendationResponse,
    PlainImmunizationRecommendationResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "ImmunizationRecommendation not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PlainImmunizationRecommendationResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRImmunizationRecommendationSchema.model_json_schema()
                )
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of immunization recommendations",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PaginatedImmunizationRecommendationResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRImmunizationRecommendationBundle.model_json_schema()
                )
            },
        },
    }
}
