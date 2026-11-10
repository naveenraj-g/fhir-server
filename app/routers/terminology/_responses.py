from fastapi import HTTPException, Request

from app.core.schema_utils import inline_schema
from app.schemas.terminology import (
    CodeSystemListResponse,
    ConceptMapListResponse,
    ConceptsForFieldResponse,
    LookupBatchResponse,
    LookupResult,
    OrgConceptListResponse,
    OrgConceptResponse,
    SearchResponse,
    TranslateResponse,
    ValidateResponse,
    ValueSetExpandResponse,
    ValueSetListResponse,
)


def _require_org_id(request: Request) -> str:
    """Used by every org-scoped route (today, just org-concepts) — needs
    the caller's org from the verified JWT, 403 if absent."""
    org_id = request.state.user.get("activeOrganizationId")
    if not org_id:
        raise HTTPException(
            status_code=403,
            detail="Organization context required. Pass X-Org-ID header.",
        )
    return org_id

_CS_LIST_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(CodeSystemListResponse.model_json_schema())
            }
        }
    }
}
_VS_LIST_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(ValueSetListResponse.model_json_schema())
            }
        }
    }
}
_VS_EXPAND_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(ValueSetExpandResponse.model_json_schema())
            }
        }
    }
}
_SEARCH_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(SearchResponse.model_json_schema())
            }
        }
    }
}
_LOOKUP_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(LookupResult.model_json_schema())
            }
        }
    }
}
_LOOKUP_BATCH_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(LookupBatchResponse.model_json_schema())
            }
        }
    }
}
_CONCEPTS_FIELD_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(ConceptsForFieldResponse.model_json_schema())
            }
        }
    }
}
_VALIDATE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(ValidateResponse.model_json_schema())
            }
        }
    }
}
_TRANSLATE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(TranslateResponse.model_json_schema())
            }
        }
    }
}
_CONCEPT_MAPS_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(ConceptMapListResponse.model_json_schema())
            }
        }
    }
}
_ORG_CONCEPT_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(OrgConceptListResponse.model_json_schema())
            }
        }
    }
}
_ORG_CONCEPT_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(OrgConceptResponse.model_json_schema())
            }
        }
    }
}
