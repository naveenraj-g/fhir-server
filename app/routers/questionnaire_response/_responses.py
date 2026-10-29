from app.core.schema_utils import inline_schema
from app.schemas.questionnaire_response import (
    FHIRQuestionnaireResponseBundle,
    FHIRQuestionnaireResponseSchema,
    PaginatedQuestionnaireResponseResponse,
    PlainQuestionnaireResponseResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "QuestionnaireResponse not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(PlainQuestionnaireResponseResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRQuestionnaireResponseSchema.model_json_schema())
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of questionnaire responses",
        "content": {
            "application/json": {
                "schema": inline_schema(PaginatedQuestionnaireResponseResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRQuestionnaireResponseBundle.model_json_schema())
            },
        },
    }
}
