from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.specimen import get_specimen_service
from app.schemas.specimen import SpecimenCreateSchema, SpecimenPatchSchema
from app.services.specimen import SpecimenService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
)

router = APIRouter()

logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_specimen",
    summary="Create a new Specimen resource",
    description=(
        "Sample to be used for analysis. "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_specimen(
    payload: SpecimenCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen", "create")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    logger.info("Create a new Specimen resource", extra={"event": "route.create_specimen"})
    log_payload(logger, "specimen.create.payload", payload)
    specimen = await specimen_service.create_specimen(payload, actor.org_id, actor.sub)
    return format_response(
        specimen_service._to_fhir(specimen),
        specimen_service._to_plain(specimen),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{specimen_id}",
    operation_id="get_specimen_by_id",
    summary="Retrieve a Specimen resource by public specimen_id",
    description=(
        "Scoped to the caller's own org — get_specimen_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_specimen(
    request: Request,
    specimen_id: int = Path(..., ge=1, description="Public specimen identifier."),
    actor: AuthUser = Depends(require_permission("specimen", "read")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    logger.info(
        "Retrieve a Specimen resource by public specimen_id",
        extra={"event": "route.get_specimen_by_id", "specimen_id": specimen_id},
    )
    specimen = await specimen_service.get_specimen_scoped(specimen_id, actor.org_id)
    return format_response(
        specimen_service._to_fhir(specimen),
        specimen_service._to_plain(specimen),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{specimen_id}",
    operation_id="patch_specimen",
    summary="Update a Specimen resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_specimen(
    payload: SpecimenPatchSchema,
    request: Request,
    specimen_id: int = Path(..., ge=1, description="Public specimen identifier."),
    actor: AuthUser = Depends(require_permission("specimen", "update")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    logger.info(
        "Update a Specimen resource",
        extra={"event": "route.patch_specimen", "specimen_id": specimen_id},
    )
    log_payload(logger, "specimen.patch.payload", payload)
    updated = await specimen_service.patch_specimen(
        specimen_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        specimen_service._to_fhir(updated),
        specimen_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_specimens",
    summary="List all Specimen resources",
    description=(
        "Returns a paginated list of Specimen resources. Filter by status, type, "
        "subject, accession_identifier, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_specimens(
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen", "read")),
    status: str | None = Query(None, description="Status code, e.g. available, unavailable."),
    type: str | None = Query(None, description="Specimen type code."),
    subject: str | None = Query(None, description="Exact match on subject reference string."),
    accession_identifier: str | None = Query(None, description="Exact match on accession identifier value."),
    identifier: str | None = Query(None, description="Exact match on business identifier value."),
    params: ListParams = Depends(),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    logger.info("List all Specimen resources", extra={"event": "route.list_specimens"})
    items, total = await specimen_service.list_specimens(
        org_id=actor.org_id,
        status=status,
        type=type,
        subject=subject,
        accession_identifier=accession_identifier,
        identifier=identifier,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [specimen_service._to_fhir(s) for s in items],
        [specimen_service._to_plain(s) for s in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{specimen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_specimen",
    summary="Delete a Specimen resource",
    description=(
        "Permanently deletes the Specimen and all associated sub-resources. Scoped "
        "to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_specimen(
    specimen_id: int = Path(..., ge=1, description="Public specimen identifier."),
    actor: AuthUser = Depends(require_permission("specimen", "delete")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    logger.info(
        "Delete a Specimen resource",
        extra={"event": "route.delete_specimen", "specimen_id": specimen_id},
    )
    await specimen_service.delete_specimen(specimen_id, org_id=actor.org_id)
