from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.deps.medication_request_deps import resolve_medication_request
from app.di.dependencies.medication_request import get_medication_request_service
from app.models.medication_request import MedicationRequestModel
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
        "transaction. Default (gateway-trusted) pattern: `tenant_id`/`created_by` are plain "
        "request body fields. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_medication_request(
    payload: MedicationRequestCreateSchema,
    request: Request,
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info("Create a new MedicationRequest resource", extra={"event": "route.create_medication_request"})
    log_payload(logger, "medication_request.create.payload", payload)
    medication_request = await medication_request_service.create_medication_request(payload)
    return format_response(
        medication_request_service._to_fhir(medication_request),
        medication_request_service._to_plain(medication_request),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Me (must come before /{medication_request_id}) ──────────────────────────────


@router.get(
    "/me",
    operation_id="list_my_medication_requests",
    summary="List MedicationRequest resources owned by a given end-user",
    description=(
        "Same filters as `GET /`, scoped to the gateway-forwarded `user_id` query param "
        "(default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_medication_requests(
    request: Request,
    user_id: str = Query(..., description="Gateway-forwarded ID of the end-user to scope results to."),
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID."),
    medication_request_status: MedicationRequestStatus | None = Query(
        None, alias="status", description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown."
    ),
    intent: MedicationRequestIntent | None = Query(None, description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option."),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info("List MedicationRequest resources owned by a given end-user", extra={"event": "route.list_my_medication_requests"})
    items, total = await medication_request_service.get_me(
        user_id=user_id, tenant_id=tenant_id, status=medication_request_status, intent=intent,
        subject=subject, identifier=identifier, limit=params.limit, offset=params.offset,
        sort=params.sort, total_mode=params.total_mode,
    )
    return format_paginated_response(
        [medication_request_service._to_fhir(mr) for mr in items],
        [medication_request_service._to_plain(mr) for mr in items],
        total, params.limit, params.offset, request,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_request_id}",
    operation_id="get_medication_request_by_id",
    summary="Retrieve a MedicationRequest resource by public medication_request_id",
    description=(
        "Loaded via `resolve_medication_request()` — a plain load-by-public-ID lookup with "
        "no ownership check (default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication_request(
    request: Request,
    medication_request: MedicationRequestModel = Depends(resolve_medication_request),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info(
        "Retrieve a MedicationRequest resource by public medication_request_id",
        extra={"event": "route.get_medication_request_by_id", "medication_request_id": medication_request.medication_request_id},
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
        "omitted lists are left untouched. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_request(
    payload: MedicationRequestPatchSchema,
    request: Request,
    medication_request_id: int = Path(..., ge=1, description="Public medication_request identifier."),
    _existing: MedicationRequestModel = Depends(resolve_medication_request),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info("Update a MedicationRequest resource", extra={"event": "route.patch_medication_request", "medication_request_id": medication_request_id})
    log_payload(logger, "medication_request.patch.payload", payload)
    updated = await medication_request_service.patch_medication_request(medication_request_id, payload)
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
        "identifier value), plus `tenant_id`/`user_id` as explicit, gateway-forwarded query "
        "filters. Sort with `sort` (e.g. `-authored_on`); set `total_mode=none` to skip the "
        "COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_medication_requests(
    request: Request,
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID filter."),
    user_id: str | None = Query(None, description="Gateway-forwarded end-user ID filter."),
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
        tenant_id=tenant_id, user_id=user_id, status=medication_request_status, intent=intent,
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
    description="Permanently deletes the MedicationRequest and all associated sub-resources. Returns 204 on success.",
    responses={**_ERR_NOT_FOUND},
)
async def delete_medication_request(
    medication_request_id: int = Path(..., ge=1, description="Public medication_request identifier."),
    _existing: MedicationRequestModel = Depends(resolve_medication_request),
    medication_request_service: MedicationRequestService = Depends(get_medication_request_service),
):
    logger.info("Delete a MedicationRequest resource", extra={"event": "route.delete_medication_request", "medication_request_id": medication_request_id})
    await medication_request_service.delete_medication_request(medication_request_id)
