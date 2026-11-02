from datetime import date, datetime

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.immunization import get_immunization_service
from app.schemas.immunization import (
    ImmunizationCreateSchema,
    ImmunizationPatchSchema,
)
from app.services.immunization import ImmunizationService

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
    operation_id="create_immunization",
    summary="Create a new Immunization resource",
    description=(
        "Record of an immunization event. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_immunization(
    payload: ImmunizationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization", "create")),
    immunization_service: ImmunizationService = Depends(
        get_immunization_service
    ),
):
    logger.info(
        "Create a new Immunization resource",
        extra={"event": "route.create_immunization", "org_id": actor.org_id},
    )
    log_payload(logger, "immunization.create.payload", payload)
    model = await immunization_service.create_immunization(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        immunization_service._to_fhir(model),
        immunization_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{immunization_id}",
    operation_id="get_immunization",
    summary="Get an Immunization resource by ID",
    description=(
        "Returns the complete Immunization representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_immunization(
    request: Request,
    immunization_id: int = Path(
        ..., ge=1, description="Public Immunization identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization", "read")),
    immunization_service: ImmunizationService = Depends(
        get_immunization_service
    ),
):
    logger.info(
        "Get an Immunization resource by ID",
        extra={
            "event": "route.get_immunization",
            "immunization_id": immunization_id,
        },
    )
    model = await immunization_service.get_immunization_scoped(
        immunization_id, actor.org_id
    )
    return format_response(
        immunization_service._to_fhir(model),
        immunization_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{immunization_id}",
    operation_id="patch_immunization",
    summary="Update an Immunization resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_immunization(
    payload: ImmunizationPatchSchema,
    request: Request,
    immunization_id: int = Path(
        ..., ge=1, description="Public Immunization identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization", "update")),
    immunization_service: ImmunizationService = Depends(
        get_immunization_service
    ),
):
    logger.info(
        "Update an Immunization resource",
        extra={
            "event": "route.patch_immunization",
            "immunization_id": immunization_id,
        },
    )
    log_payload(logger, "immunization.patch.payload", payload)
    updated = await immunization_service.patch_immunization(
        immunization_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        immunization_service._to_fhir(updated),
        immunization_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_immunizations",
    summary="List all Immunization resources",
    description=(
        "Returns a paginated list of Immunization resources. Filter by status, "
        "patient, vaccine_code, date, location, manufacturer, identifier. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_immunizations(
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization", "read")),
    immunization_status: str | None = Query(
        None,
        alias="status",
        description="completed | entered-in-error | not-done.",
    ),
    patient: str | None = Query(
        None, description="Patient who was administered the vaccine."
    ),
    vaccine_code: str | None = Query(
        None, description="Vaccine that was administered (system|code or code)."
    ),
    date_val: date | None = Query(
        None, alias="date", description="Vaccination administration date."
    ),
    date_from: datetime | None = Query(
        None, description="Administration date range start."
    ),
    date_to: datetime | None = Query(
        None, description="Administration date range end."
    ),
    location: str | None = Query(
        None, description="Where the vaccination occurred (Location reference or ID)."
    ),
    manufacturer: str | None = Query(
        None, description="Vaccine manufacturer (Organization reference or ID)."
    ),
    identifier: str | None = Query(
        None, description="Business identifier value."
    ),
    list_params: ListParams = Depends(),
    immunization_service: ImmunizationService = Depends(
        get_immunization_service
    ),
):
    logger.info(
        "List Immunization resources",
        extra={"event": "route.list_immunizations", "org_id": actor.org_id},
    )
    items, total = await immunization_service.list_immunizations(
        org_id=actor.org_id,
        status=immunization_status,
        patient=patient,
        vaccine_code=vaccine_code,
        date_val=date_val,
        date_from=date_from,
        date_to=date_to,
        location=location,
        manufacturer=manufacturer,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [immunization_service._to_fhir(m) for m in items],
        [immunization_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{immunization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_immunization",
    summary="Delete an Immunization resource",
    description=(
        "Deletes an Immunization and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "Immunization deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_immunization(
    immunization_id: int = Path(
        ..., ge=1, description="Public Immunization identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization", "delete")),
    immunization_service: ImmunizationService = Depends(
        get_immunization_service
    ),
):
    logger.info(
        "Delete an Immunization resource",
        extra={
            "event": "route.delete_immunization",
            "immunization_id": immunization_id,
        },
    )
    await immunization_service.delete_immunization(
        immunization_id, org_id=actor.org_id
    )
    return None
