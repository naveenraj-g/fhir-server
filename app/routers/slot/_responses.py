from typing import Annotated

from pydantic import StringConstraints

from app.core.schema_utils import inline_schema
from app.schemas.slot import (
    FHIRSlotBundle,
    FHIRSlotSchema,
    PaginatedSlotResponse,
    PlainSlotResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

# FHIR comparator-prefixed date, e.g. "ge2024-06-01" or "2024-06-01T09:00:00Z" —
# see app.core.filters.apply_fhir_date_filter, which does the actual parsing;
# this pattern just rejects an obviously malformed value at parameter-binding
# time. start/end are repeatable (list[str]) query params — Query()'s own
# `pattern=` kwarg only constrains scalar params, not list items, so each item
# needs its own StringConstraints via Annotated instead. Mirrors
# app.routers.patient._responses._FhirDateItem.
_FHIR_DATE_PATTERN = (
    r"^(eq|ne|gt|lt|ge|le)?\d{4}-\d{2}-\d{2}"
    r"(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
)
_FhirDateItem = Annotated[str, StringConstraints(pattern=_FHIR_DATE_PATTERN)]

# FHIR reference string, e.g. "Schedule/200001" — see
# app.core.filters.parse_reference, which validates the resource-type half
# against the caller-supplied enum; this pattern only rejects the gross shape.
_FHIR_REFERENCE_PATTERN = r"^[A-Za-z]+/\d+$"

_ERR_NOT_FOUND = {404: {"description": "Slot not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(PlainSlotResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRSlotSchema.model_json_schema())
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of slots",
        "content": {
            "application/json": {
                "schema": inline_schema(PaginatedSlotResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRSlotBundle.model_json_schema())
            },
        },
    }
}
