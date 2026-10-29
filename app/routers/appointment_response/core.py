from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.appointment_response import get_appointment_response_service
from app.schemas.appointment_response import (
    AppointmentResponseCreateSchema,
    AppointmentResponsePatchSchema,
)
from app.schemas.enums import AppointmentResponseParticipantStatus
from app.services.appointment_response import AppointmentResponseService

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
    operation_id="create_appointment_response",
    summary="Create a new AppointmentResponse resource",
    description=(
        "A reply to an appointment request for a patient and/or practitioner(s), "
        "such as a confirmation or rejection. AppointmentResponse is set once and "
        "then patched rather than built up incrementally, so this single endpoint "
        "accepts the full nested payload — identifier and participantType arrays "
        "— atomically in one DB transaction. `appointment` (e.g. 'Appointment/40001') "
        "and `participant_status` are required; `appointment` is rejected with 422 "
        "if it doesn't exist in this org. Per apr-1, either `participant_type` or "
        "`actor` must be supplied (enforced by base R4 validation). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_appointment_response(
    payload: AppointmentResponseCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("appointment_response", "create")),
    appointment_response_service: AppointmentResponseService = Depends(
        get_appointment_response_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). AppointmentResponse has no
    user_id field at all, like Organization/Location/.../Appointment."""
    logger.info(
        "Create a new AppointmentResponse resource",
        extra={"event": "route.create_appointment_response"},
    )
    log_payload(logger, "appointment_response.create.payload", payload)
    appointment_response = await appointment_response_service.create_appointment_response(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        appointment_response_service._to_fhir(appointment_response),
        appointment_response_service._to_plain(appointment_response),
        request,
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/{appointment_response_id}",
    operation_id="get_appointment_response_by_id",
    summary="Retrieve an AppointmentResponse resource by public appointment_response_id",
    description=(
        "Scoped to the caller's own org — get_appointment_response_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_appointment_response(
    request: Request,
    appointment_response_id: int = Path(
        ..., ge=1, description="Public appointment response identifier."
    ),
    actor: AuthUser = Depends(require_permission("appointment_response", "read")),
    appointment_response_service: AppointmentResponseService = Depends(
        get_appointment_response_service
    ),
):
    logger.info(
        "Retrieve an AppointmentResponse resource by public appointment_response_id",
        extra={
            "event": "route.get_appointment_response_by_id",
            "appointment_response_id": appointment_response_id,
        },
    )
    appointment_response = await appointment_response_service.get_appointment_response_scoped(
        appointment_response_id, actor.org_id
    )
    return format_response(
        appointment_response_service._to_fhir(appointment_response),
        appointment_response_service._to_plain(appointment_response),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{appointment_response_id}",
    operation_id="patch_appointment_response",
    summary="Update an AppointmentResponse resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (identifier, participantType — even `[]`) "
        "atomically replaces the corresponding rows; omitted lists are left "
        "untouched. Scoped to the caller's own org — patch_appointment_response() "
        "raises NotFoundError (404, not 403 — avoids leaking that a row with this "
        "id exists in another org) if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_appointment_response(
    payload: AppointmentResponsePatchSchema,
    request: Request,
    appointment_response_id: int = Path(
        ..., ge=1, description="Public appointment response identifier."
    ),
    actor: AuthUser = Depends(require_permission("appointment_response", "update")),
    appointment_response_service: AppointmentResponseService = Depends(
        get_appointment_response_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub);
    patch_appointment_response() raises NotFoundError (404, not 403) if
    actor.org_id doesn't match."""
    logger.info(
        "Update an AppointmentResponse resource",
        extra={
            "event": "route.patch_appointment_response",
            "appointment_response_id": appointment_response_id,
        },
    )
    log_payload(logger, "appointment_response.patch.payload", payload)
    updated = await appointment_response_service.patch_appointment_response(
        appointment_response_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        appointment_response_service._to_fhir(updated),
        appointment_response_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_appointment_responses",
    summary="List all AppointmentResponse resources",
    description=(
        "Returns a paginated list of AppointmentResponse resources, matching a "
        "subset of the search parameter set documented at "
        "https://www.hl7.org/fhir/R4/appointmentresponse.html#search. "
        "Filter by `identifier` (exact business-identifier value), `appointment` "
        "(FHIR reference string, e.g. `Appointment/40001`), `actor` (FHIR "
        "reference string, e.g. `Practitioner/30001`), `part-status`. "
        "Always scoped to the caller's own org (from the verified token) — `org_id` "
        "is not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-created_at`); set `total_mode=none` to skip the "
        "COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_appointment_responses(
    request: Request,
    actor: AuthUser = Depends(require_permission("appointment_response", "read")),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    appointment: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Appointment/40001`.",
    ),
    actor_ref: str | None = Query(
        None,
        alias="actor",
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Practitioner/30001`.",
    ),
    part_status: AppointmentResponseParticipantStatus | None = Query(
        None,
        alias="part-status",
        description="accepted | declined | tentative | needs-action.",
    ),
    params: ListParams = Depends(),
    appointment_response_service: AppointmentResponseService = Depends(
        get_appointment_response_service
    ),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_appointment_responses() raises PermissionDeniedError (403)
    outright for an org-less token."""
    logger.info(
        "List all AppointmentResponse resources",
        extra={"event": "route.list_appointment_responses"},
    )
    items, total = await appointment_response_service.list_appointment_responses(
        org_id=actor.org_id,
        identifier=identifier,
        appointment=appointment,
        actor=actor_ref,
        part_status=part_status,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [appointment_response_service._to_fhir(a) for a in items],
        [appointment_response_service._to_plain(a) for a in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{appointment_response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_appointment_response",
    summary="Delete an AppointmentResponse resource",
    description=(
        "Permanently deletes the AppointmentResponse and all associated "
        "sub-resources. Scoped to the caller's own org — raises NotFoundError "
        "(404, not 403) if it exists but belongs to a different org. Returns "
        "204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_appointment_response(
    appointment_response_id: int = Path(
        ..., ge=1, description="Public appointment response identifier."
    ),
    actor: AuthUser = Depends(require_permission("appointment_response", "delete")),
    appointment_response_service: AppointmentResponseService = Depends(
        get_appointment_response_service
    ),
):
    """delete_appointment_response() raises NotFoundError (404) if the id
    doesn't exist at all, or if it exists but belongs to a different org.
    Delete cascades to every sub-resource row."""
    logger.info(
        "Delete an AppointmentResponse resource",
        extra={
            "event": "route.delete_appointment_response",
            "appointment_response_id": appointment_response_id,
        },
    )
    await appointment_response_service.delete_appointment_response(
        appointment_response_id, org_id=actor.org_id
    )
