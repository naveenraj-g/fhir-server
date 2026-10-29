from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.appointment import get_appointment_service
from app.schemas.appointment import AppointmentCreateSchema, AppointmentPatchSchema
from app.schemas.enums import AppointmentStatus
from app.services.appointment import AppointmentService

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
    operation_id="create_appointment",
    summary="Create a new Appointment resource",
    description=(
        "A booking of a healthcare event among patient(s), practitioner(s), related "
        "person(s) and/or device(s) for a specific date/time. Appointment is set once "
        "and then patched rather than built up incrementally, so this single endpoint "
        "accepts the full nested payload — identifier, serviceCategory, serviceType, "
        "specialty, reasonCode, reasonReference, supportingInformation, slot, basedOn, "
        "requestedPeriod, and participant arrays, plus the flattened cancelationReason "
        "and appointmentType CodeableConcepts — atomically in one DB transaction. "
        "`status` is required; `participant` is 1..* per spec (not enforced at the "
        "schema layer, but by base R4 validation before the write commits). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_appointment(
    payload: AppointmentCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("appointment", "create")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). Appointment has no user_id
    field at all, like Organization/Location/HealthcareService/
    PractitionerRole/Schedule/Slot."""
    logger.info(
        "Create a new Appointment resource",
        extra={"event": "route.create_appointment"},
    )
    log_payload(logger, "appointment.create.payload", payload)
    appointment = await appointment_service.create_appointment(payload, actor.org_id, actor.sub)
    return format_response(
        appointment_service._to_fhir(appointment),
        appointment_service._to_plain(appointment),
        request,
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/{appointment_id}",
    operation_id="get_appointment_by_id",
    summary="Retrieve an Appointment resource by public appointment_id",
    description=(
        "Scoped to the caller's own org — get_appointment_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_appointment(
    request: Request,
    appointment_id: int = Path(..., ge=1, description="Public appointment identifier."),
    actor: AuthUser = Depends(require_permission("appointment", "read")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    logger.info(
        "Retrieve an Appointment resource by public appointment_id",
        extra={"event": "route.get_appointment_by_id", "appointment_id": appointment_id},
    )
    appointment = await appointment_service.get_appointment_scoped(appointment_id, actor.org_id)
    return format_response(
        appointment_service._to_fhir(appointment),
        appointment_service._to_plain(appointment),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{appointment_id}",
    operation_id="patch_appointment",
    summary="Update an Appointment resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (even `[]`) atomically replaces the corresponding "
        "rows; omitted lists are left untouched. "
        "Scoped to the caller's own org — patch_appointment() raises NotFoundError "
        "(404, not 403 — avoids leaking that an appointment with this id exists in "
        "another org) if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_appointment(
    payload: AppointmentPatchSchema,
    request: Request,
    appointment_id: int = Path(..., ge=1, description="Public appointment identifier."),
    actor: AuthUser = Depends(require_permission("appointment", "update")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_appointment()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an Appointment resource",
        extra={"event": "route.patch_appointment", "appointment_id": appointment_id},
    )
    log_payload(logger, "appointment.patch.payload", payload)
    updated = await appointment_service.patch_appointment(
        appointment_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        appointment_service._to_fhir(updated), appointment_service._to_plain(updated), request
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_appointments",
    summary="List all Appointment resources",
    description=(
        "Returns a paginated list of Appointment resources, matching a subset of the "
        "search parameter set documented at "
        "https://www.hl7.org/fhir/R4/appointment.html#search. "
        "Filter by `status`, `identifier` (exact business-identifier value), "
        "`service-category`/`service-type`/`specialty` (exact code match), "
        "`actor` (FHIR reference string, e.g. `Practitioner/30001`), "
        "`slot` (FHIR reference string, e.g. `Slot/220001`). "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is "
        "not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-start`); set `total_mode=none` to skip the COUNT(*) "
        "on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_appointments(
    request: Request,
    actor: AuthUser = Depends(require_permission("appointment", "read")),
    appointment_status: AppointmentStatus | None = Query(
        None,
        alias="status",
        description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | entered-in-error | checked-in | waitlist.",
    ),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    service_category: str | None = Query(
        None, alias="service-category", description="Exact match on a coded service category."
    ),
    service_type: str | None = Query(
        None, alias="service-type", description="Exact match on a coded service type."
    ),
    specialty: str | None = Query(None, description="Exact match on a coded specialty."),
    actor_ref: str | None = Query(
        None,
        alias="actor",
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Practitioner/30001`.",
    ),
    slot: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Slot/220001`.",
    ),
    params: ListParams = Depends(),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_appointments() raises PermissionDeniedError (403) outright for an
    org-less token."""
    logger.info(
        "List all Appointment resources",
        extra={"event": "route.list_appointments"},
    )
    items, total = await appointment_service.list_appointments(
        org_id=actor.org_id,
        status=appointment_status,
        identifier=identifier,
        service_category=service_category,
        service_type=service_type,
        specialty=specialty,
        actor=actor_ref,
        slot=slot,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [appointment_service._to_fhir(a) for a in items],
        [appointment_service._to_plain(a) for a in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_appointment",
    summary="Delete an Appointment resource",
    description=(
        "Permanently deletes the Appointment and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "appointment exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_appointment(
    appointment_id: int = Path(..., ge=1, description="Public appointment identifier."),
    actor: AuthUser = Depends(require_permission("appointment", "delete")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """delete_appointment() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org. Delete
    cascades to every sub-resource row."""
    logger.info(
        "Delete an Appointment resource",
        extra={"event": "route.delete_appointment", "appointment_id": appointment_id},
    )
    await appointment_service.delete_appointment(appointment_id, org_id=actor.org_id)
