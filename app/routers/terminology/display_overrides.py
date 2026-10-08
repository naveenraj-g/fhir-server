from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from app.di.dependencies.terminology import get_terminology_client
from app.schemas.terminology import (
    CreateDisplayOverrideRequest,
    PatchDisplayOverrideRequest,
)
from app.terminology.client import TerminologyClient

from ._responses import (
    _DISPLAY_OVERRIDE_200,
    _DISPLAY_OVERRIDE_SINGLE_200,
    _require_org_id,
)

router = APIRouter()


@router.get(
    "/display-overrides",
    operation_id="list_display_overrides",
    summary="List this org's display overrides",
    description=(
        "Returns all display-label overrides this org has defined for existing codes "
        "(e.g. a custom label for an HL7 status code, without changing the code itself)."
    ),
    responses=_DISPLAY_OVERRIDE_200,
    tags=["Terminology"],
)
async def list_display_overrides(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    result = await service.list_display_overrides(org_id, limit, offset)
    return JSONResponse(content=jsonable_encoder(result))


@router.post(
    "/display-overrides",
    operation_id="create_display_override",
    summary="Create a display override for an existing code",
    description=(
        "Relabels an existing code (identified by system+code) for this org only — the "
        "underlying code is unchanged, only the display shown to this org's users differs. "
        "The system+code must already exist (e.g. an HL7 required-binding status code); "
        "this cannot be used to invent a new code — see POST /org-concepts for that."
    ),
    responses={
        201: _DISPLAY_OVERRIDE_SINGLE_200[200],
        403: {"description": "Organization context required (X-Org-ID header missing)"},
        404: {"description": "No concept found for the given system+code"},
    },
    tags=["Terminology"],
)
async def create_display_override(
    body: CreateDisplayOverrideRequest,
    request: Request,
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    user_id = request.state.user.get("sub")
    result = await service.create_display_override(body, org_id, user_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No concept found for system={body.system!r}, code={body.code!r}.",
        )
    return JSONResponse(content=jsonable_encoder(result), status_code=201)


@router.get(
    "/display-overrides/{override_id}",
    operation_id="get_display_override",
    summary="Get a single display override",
    description="Returns a display override by its database ID. Only returns overrides belonging to the caller's org.",
    responses={
        **_DISPLAY_OVERRIDE_SINGLE_200,
        404: {"description": "Override not found"},
    },
    tags=["Terminology"],
)
async def get_display_override(
    override_id: int,
    request: Request,
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    result = await service.get_display_override(override_id, org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Override not found.")
    return JSONResponse(content=jsonable_encoder(result))


@router.patch(
    "/display-overrides/{override_id}",
    operation_id="patch_display_override",
    summary="Update a display override",
    description="Updates the display label or definition of an override. Only the creating organization can update it.",
    responses={
        **_DISPLAY_OVERRIDE_SINGLE_200,
        404: {"description": "Override not found"},
    },
    tags=["Terminology"],
)
async def patch_display_override(
    override_id: int,
    body: PatchDisplayOverrideRequest,
    request: Request,
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    result = await service.patch_display_override(override_id, body, org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Override not found.")
    return JSONResponse(content=jsonable_encoder(result))


@router.delete(
    "/display-overrides/{override_id}",
    operation_id="delete_display_override",
    summary="Delete a display override",
    description="Permanently removes a display override. Only the creating organization can delete it.",
    responses={
        204: {"description": "Deleted"},
        404: {"description": "Override not found"},
    },
    tags=["Terminology"],
)
async def delete_display_override(
    override_id: int,
    request: Request,
    service: TerminologyClient = Depends(get_terminology_client),
):
    org_id = _require_org_id(request)
    deleted = await service.delete_display_override(override_id, org_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Override not found.")
    return Response(status_code=204)
