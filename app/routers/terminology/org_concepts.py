from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from app.core.schema_utils import inline_schema
from app.di.dependencies.terminology import get_terminology_client
from app.schemas.terminology import (
    CreateConceptRequest,
    OrgConceptResponse,
    PatchConceptRequest,
)
from app.terminology.client import TerminologyClient

from ._responses import _ORG_CONCEPT_200, _ORG_CONCEPT_SINGLE_200, _require_org_id

router = APIRouter()


@router.get(
    "/org-concepts",
    operation_id="list_org_concepts",
    summary="List this org's custom terminology concepts",
    description=(
        "Returns all custom concepts created by the organization identified by the X-Org-ID header. "
        "Supports filtering by code system and full-text search."
    ),
    responses=_ORG_CONCEPT_200,
    tags=["Terminology"],
)
async def list_org_concepts(
    request: Request,
    code_system_url: str | None = Query(
        None, description="Filter by code system canonical URL"
    ),
    q: str | None = Query(None, description="Full-text search"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    result = await service.list_org_concepts(org_id, code_system_url, q, limit, offset)
    return JSONResponse(content=jsonable_encoder(result))


@router.post(
    "/org-concepts",
    operation_id="create_org_concept",
    summary="Create an org-specific custom concept",
    description=(
        "Adds a custom terminology code scoped to the organization identified by the X-Org-ID header. "
        "The code_system_url must reference an existing code system in the database. "
        "The code must be unique within the org's namespace for that code system."
    ),
    responses={
        201: {
            "content": {
                "application/json": {
                    "schema": inline_schema(OrgConceptResponse.model_json_schema())
                }
            }
        },
        403: {"description": "Organization context required (X-Org-ID header missing)"},
        404: {"description": "Code system not found"},
        409: {"description": "Code already exists for this org and code system"},
    },
    tags=["Terminology"],
)
async def create_org_concept(
    body: CreateConceptRequest,
    request: Request,
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    user_id = request.state.user.get("sub")
    try:
        result = await service.create_concept(body, org_id, user_id)
    except Exception as exc:
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Code '{body.code}' already exists for this org in {body.code_system_url}.",
            )
        raise
    if result is None:
        raise HTTPException(
            status_code=404, detail=f"Code system not found: {body.code_system_url}"
        )
    return JSONResponse(content=jsonable_encoder(result), status_code=201)


@router.get(
    "/org-concepts/{concept_id}",
    operation_id="get_org_concept",
    summary="Get a single org-specific concept",
    description="Returns a custom concept by its database ID. Only returns concepts belonging to the org in X-Org-ID header.",
    responses={**_ORG_CONCEPT_SINGLE_200, 404: {"description": "Concept not found"}},
    tags=["Terminology"],
)
async def get_org_concept(
    concept_id: int,
    request: Request,
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    result = await service.get_org_concept(concept_id, org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Concept not found.")
    return JSONResponse(content=jsonable_encoder(result))


@router.patch(
    "/org-concepts/{concept_id}",
    operation_id="patch_org_concept",
    summary="Update an org-specific concept",
    description="Updates the display name or definition of a custom concept. Only the creating organization can update it.",
    responses={**_ORG_CONCEPT_SINGLE_200, 404: {"description": "Concept not found"}},
    tags=["Terminology"],
)
async def patch_org_concept(
    concept_id: int,
    body: PatchConceptRequest,
    request: Request,
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    result = await service.patch_concept(concept_id, body, org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Concept not found.")
    return JSONResponse(content=jsonable_encoder(result))


@router.delete(
    "/org-concepts/{concept_id}",
    operation_id="delete_org_concept",
    summary="Delete an org-specific concept",
    description="Permanently removes a custom concept. Only the creating organization can delete it.",
    responses={
        204: {"description": "Deleted"},
        404: {"description": "Concept not found"},
    },
    tags=["Terminology"],
)
async def delete_org_concept(
    concept_id: int,
    request: Request,
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    deleted = await service.delete_concept(concept_id, org_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Concept not found.")
    return Response(status_code=204)
