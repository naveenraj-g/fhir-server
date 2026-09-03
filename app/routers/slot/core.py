from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.slot import get_slot_service
from app.models.slot.enums import SlotStatus
from app.schemas.slot import SlotCreateSchema, SlotPatchSchema
from app.services.slot import SlotService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _FhirDateItem,
    _FHIR_REFERENCE_PATTERN,
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
    operation_id="create_slot",
    summary="Create a new Slot resource",
    description=(
        "A slot of time on a schedule that may be available for booking appointments. "
        "Slot is set once and then patched rather than built up incrementally, so this "
        "single endpoint accepts the full nested payload — identifier, serviceCategory, "
        "serviceType, and specialty arrays — atomically in one DB transaction. "
        "`schedule` (a reference to the Schedule this slot belongs to, e.g. "
        "'Schedule/200001'), `status`, `start`, and `end` are all required (FHIR R4 "
        "Slot.schedule/status/start/end are all 1..1) — the `schedule` reference is "
        "rejected with 422 if it doesn't resolve to an existing Schedule in this org. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_slot(
    payload: SlotCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("slot", "create")),
    slot_service: SlotService = Depends(get_slot_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403). Slot has no user_id field at all, like
    Organization, Location, HealthcareService, PractitionerRole, and
    Schedule."""
    logger.info(
        "Create a new Slot resource",
        extra={"event": "route.create_slot"},
    )
    log_payload(logger, "slot.create.payload", payload)
    slot = await slot_service.create_slot(payload, actor.org_id, actor.sub)
    return format_response(
        slot_service._to_fhir(slot),
        slot_service._to_plain(slot),
        request,
    )


@router.get(
    "/{slot_id}",
    operation_id="get_slot_by_id",
    summary="Retrieve a Slot resource by public slot_id",
    description=(
        "Scoped to the caller's own org — get_slot_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_slot(
    request: Request,
    slot_id: int = Path(..., ge=1, description="Public slot identifier."),
    actor: AuthUser = Depends(require_permission("slot", "read")),
    slot_service: SlotService = Depends(get_slot_service),
):
    logger.info(
        "Retrieve a Slot resource by public slot_id",
        extra={"event": "route.get_slot_by_id", "slot_id": slot_id},
    )
    slot = await slot_service.get_slot_scoped(slot_id, actor.org_id)
    return format_response(
        slot_service._to_fhir(slot),
        slot_service._to_plain(slot),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{slot_id}",
    operation_id="patch_slot",
    summary="Update a Slot resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (identifier, serviceCategory, serviceType, "
        "specialty — even `[]`) atomically replaces the corresponding rows; omitted "
        "lists are left untouched. The `schedule` reference cannot be changed via "
        "PATCH — delete and re-create the Slot to correct it. Scoped to the caller's "
        "own org — patch_slot() raises NotFoundError (404, not 403 — avoids leaking "
        "that a slot with this id exists in another org) if actor.org_id doesn't "
        "match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_slot(
    payload: SlotPatchSchema,
    request: Request,
    slot_id: int = Path(..., ge=1, description="Public slot identifier."),
    actor: AuthUser = Depends(require_permission("slot", "update")),
    slot_service: SlotService = Depends(get_slot_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_slot()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Slot resource",
        extra={"event": "route.patch_slot", "slot_id": slot_id},
    )
    log_payload(logger, "slot.patch.payload", payload)
    updated = await slot_service.patch_slot(
        slot_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        slot_service._to_fhir(updated),
        slot_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_slots",
    summary="List all Slot resources",
    description=(
        "Returns a paginated list of Slot resources, matching the search parameter "
        "set documented at https://www.medplum.com/docs/api/fhir/resources/slot. "
        "Filter by `appointment-type` (exact code match), `identifier` (exact "
        "business-identifier value), `schedule` (FHIR reference string, e.g. "
        "`Schedule/200001`), `service-category`/`service-type`/`specialty` (exact "
        "code match), `status`, and `start`/`end` (FHIR comparator-prefixed date, "
        "e.g. `ge2024-06-01`; repeat the param for a range). Always scoped to the "
        "caller's own org (from the verified token) — `org_id` is not a client-"
        "suppliable filter. Sort with `sort` (e.g. `-slot_id`); set "
        "`total_mode=none` to skip the COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_slots(
    request: Request,
    actor: AuthUser = Depends(require_permission("slot", "read")),
    appointment_type: str | None = Query(
        None,
        alias="appointment-type",
        description="Exact match on the appointmentType code.",
    ),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    schedule: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string to the Schedule, e.g. `Schedule/200001`.",
    ),
    service_category: str | None = Query(
        None,
        alias="service-category",
        description="Exact match on a coded service category.",
    ),
    service_type: str | None = Query(
        None,
        alias="service-type",
        description="Exact match on a coded service type.",
    ),
    specialty: str | None = Query(
        None, description="Exact match on a coded specialty."
    ),
    slot_status: SlotStatus | None = Query(
        None,
        alias="status",
        description="Filter by slot status (busy | free | busy-unavailable | busy-tentative | entered-in-error).",
    ),
    start: list[_FhirDateItem] | None = Query(
        None,
        description=(
            "FHIR comparator-prefixed date (eq/ne/gt/lt/ge/le), e.g. `ge2024-06-01`. "
            "Repeat the param for a range, e.g. `start=ge2024-06-01&start=le2024-06-30`."
        ),
    ),
    end: list[_FhirDateItem] | None = Query(
        None,
        description="Same comparator-prefixed format as start, filtering on Slot.end.",
    ),
    params: ListParams = Depends(),
    slot_service: SlotService = Depends(get_slot_service),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_slots() raises PermissionDeniedError (403) outright for an org-less
    token."""
    logger.info(
        "List all Slot resources",
        extra={"event": "route.list_slots"},
    )
    items, total = await slot_service.list_slots(
        org_id=actor.org_id,
        appointment_type=appointment_type,
        identifier=identifier,
        schedule=schedule,
        service_category=service_category,
        service_type=service_type,
        specialty=specialty,
        slot_status=slot_status,
        start=start,
        end=end,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [slot_service._to_fhir(s) for s in items],
        [slot_service._to_plain(s) for s in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_slot",
    summary="Delete a Slot resource",
    description=(
        "Permanently deletes the Slot and all associated sub-resources. Scoped to "
        "the caller's own org — raises NotFoundError (404, not 403) if the slot "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_slot(
    slot_id: int = Path(..., ge=1, description="Public slot identifier."),
    actor: AuthUser = Depends(require_permission("slot", "delete")),
    slot_service: SlotService = Depends(get_slot_service),
):
    """delete_slot() raises NotFoundError (404) if the id doesn't exist at
    all, or if it exists but belongs to a different org. Delete cascades to
    every sub-resource row."""
    logger.info(
        "Delete a Slot resource",
        extra={"event": "route.delete_slot", "slot_id": slot_id},
    )
    await slot_service.delete_slot(slot_id, org_id=actor.org_id)
