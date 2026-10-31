from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.medication_request import get_medication_request_service
from app.schemas.enums import MedicationRequestIntent, MedicationRequestStatus
from app.schemas.medication_request import MedicationRequestCreateSchema, MedicationRequestPatchSchema
from app.services.medication_request import MedicationRequestService

from ._responses import _CONTENT_NEG, _ERR_NOT_FOUND, _ERR_VALIDATION, _LIST_200, _SINGLE_200, _SINGLE_201

router = APIRouter()

logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_medication_request",
    summary="Create a new MedicationRequest resource",
    description=(
        "An order or request for both supply of a medication and the instructions for its "
        "administration to a patient. Accepts the full nested payload atomically in one DB "
        "transaction. `tenant_id`/`created_by` come from the verified JWT "
        "(`actor.org_id`/`actor.sub`) — an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_medication_request(
    payload: MedicationRequestCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_request", "create")),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info("Create a new MedicationRequest resource", extra={"event": "route.create_medication_request"})
    log_payload(logger, "medication_request.create.payload", payload)
    medication_request = await medication_request_service.create_medication_request(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        medication_request_service._to_fhir(medication_request),
        medication_request_service._to_plain(medication_request),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_request_id}",
    operation_id="get_medication_request_by_id",
    summary="Retrieve a MedicationRequest resource by public medication_request_id",
    description=(
        "Scoped to the caller's own org — get_medication_request_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication_request(
    request: Request,
    medication_request_id: int = Path(..., ge=1, description="Public medication_request identifier."),
    actor: AuthUser = Depends(require_permission("medication_request", "read")),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info(
        "Retrieve a MedicationRequest resource by public medication_request_id",
        extra={"event": "route.get_medication_request_by_id", "medication_request_id": medication_request_id},
    )
    medication_request = await medication_request_service.get_medication_request_scoped(
        medication_request_id, actor.org_id
    )
    return format_response(
        medication_request_service._to_fhir(medication_request),
        medication_request_service._to_plain(medication_request),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{medication_request_id}",
    operation_id="patch_medication_request",
    summary="Update a MedicationRequest resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (even `[]`) atomically replaces the corresponding rows; "
        "omitted lists are left untouched. Scoped to the caller's own org — "
        "patch_medication_request() raises NotFoundError (404, not 403) if actor.org_id "
        "doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_request(
    payload: MedicationRequestPatchSchema,
    request: Request,
    medication_request_id: int = Path(..., ge=1, description="Public medication_request identifier."),
    actor: AuthUser = Depends(require_permission("medication_request", "update")),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info("Update a MedicationRequest resource", extra={"event": "route.patch_medication_request", "medication_request_id": medication_request_id})
    log_payload(logger, "medication_request.patch.payload", payload)
    updated = await medication_request_service.patch_medication_request(
        medication_request_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        medication_request_service._to_fhir(updated),
        medication_request_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_medication_requests",
    summary="List all MedicationRequest resources",
    description=(
        "Returns a paginated list of MedicationRequest resources, matching a subset of the "
        "search parameters documented at https://www.hl7.org/fhir/R4/medicationrequest.html#search. "
        "Filter by `status`, `intent`, `subject` (exact), `identifier` (exact business-"
        "identifier value). Always scoped to the caller's own org (from the verified "
        "token) — `org_id` is not a client-suppliable filter. Sort with `sort` (e.g. "
        "`-authored_on`); set `total_mode=none` to skip the COUNT(*) on large result "
        "sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_medication_requests(
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_request", "read")),
    medication_request_status: MedicationRequestStatus | None = Query(
        None, alias="status", description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown."
    ),
    intent: MedicationRequestIntent | None = Query(None, description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option."),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info("List all MedicationRequest resources", extra={"event": "route.list_medication_requests"})
    items, total = await medication_request_service.list_medication_requests(
        org_id=actor.org_id, status=medication_request_status, intent=intent,
        subject=subject, identifier=identifier, limit=params.limit, offset=params.offset,
        sort=params.sort, total_mode=params.total_mode,
    )
    return format_paginated_response(
        [medication_request_service._to_fhir(mr) for mr in items],
        [medication_request_service._to_plain(mr) for mr in items],
        total, params.limit, params.offset, request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{medication_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_medication_request",
    summary="Delete a MedicationRequest resource",
    description=(
        "Permanently deletes the MedicationRequest and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "resource exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_medication_request(
    medication_request_id: int = Path(..., ge=1, description="Public medication_request identifier."),
    actor: AuthUser = Depends(require_permission("medication_request", "delete")),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info("Delete a MedicationRequest resource", extra={"event": "route.delete_medication_request", "medication_request_id": medication_request_id})
    await medication_request_service.delete_medication_request(medication_request_id, org_id=actor.org_id)
