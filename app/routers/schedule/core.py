from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.schedule import get_schedule_service
from app.schemas.schedule import ScheduleCreateSchema, SchedulePatchSchema
from app.services.schedule import ScheduleService

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

_FHIR_REFERENCE_PATTERN = r"^[A-Za-z]+/[0-9]+$"


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_schedule",
    summary="Create a new Schedule resource",
    description=(
        "A container for slots of time that may be available for booking appointments. "
        "Schedule is set once and then patched rather than built up incrementally, so "
        "this single endpoint accepts the full nested payload — identifier, "
        "serviceCategory, serviceType, specialty, and actor arrays — atomically in one "
        "DB transaction. `actor` entries may reference Practitioner, PractitionerRole, "
        "HealthcareService, or Location (rejected with 422 if the referenced resource "
        "doesn't exist); Patient, RelatedPerson, and Device aren't modeled resources in "
        "this system, so those rely on the identifier fallback fields instead. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_schedule(
    payload: ScheduleCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("schedule", "create")),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). Schedule has no user_id
    field at all, like Organization/Location/HealthcareService/
    PractitionerRole."""
    logger.info(
        "Create a new Schedule resource",
        extra={"event": "route.create_schedule"},
    )
    log_payload(logger, "schedule.create.payload", payload)
    sch = await schedule_service.create_schedule(payload, actor.org_id, actor.sub)
    return format_response(
        schedule_service._to_fhir(sch), schedule_service._to_plain(sch), request
    )


@router.get(
    "/{schedule_id}",
    operation_id="get_schedule_by_id",
    summary="Retrieve a Schedule resource by public schedule_id",
    description=(
        "Scoped to the caller's own org — get_schedule_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_schedule(
    request: Request,
    schedule_id: int = Path(..., ge=1, description="Public schedule identifier."),
    actor: AuthUser = Depends(require_permission("schedule", "read")),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    logger.info(
        "Retrieve a Schedule resource by public schedule_id",
        extra={"event": "route.get_schedule_by_id", "schedule_id": schedule_id},
    )
    sch = await schedule_service.get_schedule_scoped(schedule_id, actor.org_id)
    return format_response(
        schedule_service._to_fhir(sch), schedule_service._to_plain(sch), request
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{schedule_id}",
    operation_id="patch_schedule",
    summary="Update a Schedule resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (identifier, serviceCategory, serviceType, "
        "specialty, actor — even `[]`) atomically replaces the corresponding rows; "
        "omitted lists are left untouched. "
        "Scoped to the caller's own org — patch_schedule() raises NotFoundError "
        "(404, not 403 — avoids leaking that a schedule with this id exists in "
        "another org) if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_schedule(
    payload: SchedulePatchSchema,
    request: Request,
    schedule_id: int = Path(..., ge=1, description="Public schedule identifier."),
    actor: AuthUser = Depends(require_permission("schedule", "update")),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_schedule()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Schedule resource",
        extra={"event": "route.patch_schedule", "schedule_id": schedule_id},
    )
    log_payload(logger, "schedule.patch.payload", payload)
    updated = await schedule_service.patch_schedule(
        schedule_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        schedule_service._to_fhir(updated), schedule_service._to_plain(updated), request
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_schedules",
    summary="List all Schedule resources",
    description=(
        "Returns a paginated list of Schedule resources, matching the search "
        "parameter set documented at https://www.hl7.org/fhir/R4/schedule.html#search. "
        "Filter by `active`, `identifier` (exact business-identifier value), "
        "`service-category`/`service-type`/`specialty` (exact code match), `actor` "
        "(FHIR reference string, e.g. `Practitioner/30001` / `Location/230001`). "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is "
        "not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-schedule_id`); set `total_mode=none` to skip the "
        "COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_schedules(
    request: Request,
    actor: AuthUser = Depends(require_permission("schedule", "read")),
    active: bool | None = Query(None, description="Filter by active status."),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    service_category: str | None = Query(
        None,
        alias="service-category",
        description="Exact match on a coded service category.",
    ),
    service_type: str | None = Query(
        None, alias="service-type", description="Exact match on a coded service type."
    ),
    specialty: str | None = Query(
        None, description="Exact match on a coded specialty."
    ),
    actor_ref: str | None = Query(
        None,
        alias="actor",
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Practitioner/30001` or `Location/230001`.",
    ),
    params: ListParams = Depends(),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_schedules() raises PermissionDeniedError (403) outright for an
    org-less token."""
    logger.info(
        "List all Schedule resources",
        extra={"event": "route.list_schedules"},
    )
    items, total = await schedule_service.list_schedules(
        org_id=actor.org_id,
        active=active,
        identifier=identifier,
        service_category=service_category,
        service_type=service_type,
        specialty=specialty,
        actor=actor_ref,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [schedule_service._to_fhir(sch) for sch in items],
        [schedule_service._to_plain(sch) for sch in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_schedule",
    summary="Delete a Schedule resource",
    description=(
        "Permanently deletes the Schedule and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "schedule exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_schedule(
    schedule_id: int = Path(..., ge=1, description="Public schedule identifier."),
    actor: AuthUser = Depends(require_permission("schedule", "delete")),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    """delete_schedule() raises NotFoundError (404) if the id doesn't exist
    at all, or if it exists but belongs to a different org. Delete
    cascades to every sub-resource row."""
    logger.info(
        "Delete a Schedule resource",
        extra={"event": "route.delete_schedule", "schedule_id": schedule_id},
    )
    await schedule_service.delete_schedule(schedule_id, org_id=actor.org_id)
