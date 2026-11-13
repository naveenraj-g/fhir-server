from app.core.schema_utils import inline_schema
from app.schemas.organization import FHIROrganizationBundle, FHIROrganizationSchema

# Organization is stored Medplum-style (whole resource in `content`) and
# always responds with FHIR R4 JSON — there is no plain representation.
_CONTENT_NEG = (
    "Always responds with FHIR R4 JSON (`application/fhir+json`), whatever the Accept header "
    "says; only a client that accepts no JSON at all (e.g. `Accept: application/fhir+xml`, "
    "`_format=xml`) gets 406 Not Acceptable."
)

_ERR_NOT_ACCEPTABLE = {
    406: {
        "description": "Not Acceptable — the Accept header or `_format` rules out JSON (e.g. XML only); FHIR JSON is the only format served. Body is an OperationOutcome."
    }
}

_ERR_NOT_FOUND = {404: {"description": "Organization not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_ERR_SEARCH = {
    400: {
        "description": (
            "Search rejected — a malformed value, an unsupported modifier, or (with "
            "`Prefer: handling=strict`) an unknown parameter. Body is an OperationOutcome."
        )
    }
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/fhir+json": {
                "schema": inline_schema(FHIROrganizationSchema.model_json_schema())
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "FHIR searchset Bundle: matches (search.mode=match), _include/_revinclude results (include) and any ignored-parameter warning (outcome)",
        "content": {
            "application/fhir+json": {
                "schema": inline_schema(FHIROrganizationBundle.model_json_schema())
            },
        },
    }
}
