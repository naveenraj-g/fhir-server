from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.deps.observation_deps import resolve_observation
from app.di.dependencies.observation import get_observation_service
from app.models.observation import ObservationModel
from app.schemas.enums import ObservationStatus
from app.schemas.observation import ObservationCreateSchema, ObservationPatchSchema
from app.services.observation import ObservationService

from ._responses import _CONTENT_NEG, _ERR_NOT_FOUND, _ERR_VALIDATION, _LIST_200, _SINGLE_200, _SINGLE_201

router = APIRouter()

logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_observation",
    summary="Create a new Observation resource",
    description=(
        "Measurements and simple assertions made about a patient, device or other subject. "
        "Accepts the full nested payload atomically in one DB transaction. Default "
        "(gateway-trusted) pattern: `tenant_id`/`created_by` are plain request body fields. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_observation(
    payload: ObservationCreateSchema,
    request: Request,
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info("Create a new Observation resource", extra={"event": "route.create_observation"})
    log_payload(logger, "observation.create.payload", payload)
    observation = await observation_service.create_observation(payload)
    return format_response(
        observation_service._to_fhir(observation),
        observation_service._to_plain(observation),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Me (must come before /{observation_id}) ─────────────────────────────────────


@router.get(
    "/me",
    operation_id="list_my_observations",
    summary="List Observation resources owned by a given end-user",
    description=(
        "Same filters as `GET /`, scoped to the gateway-forwarded `user_id` query param "
        "(default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_observations(
    request: Request,
    user_id: str = Query(..., description="Gateway-forwarded ID of the end-user to scope results to."),
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID."),
    observation_status: ObservationStatus | None = Query(
        None, alias="status", description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown."
    ),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info("List Observation resources owned by a given end-user", extra={"event": "route.list_my_observations"})
    items, total = await observation_service.get_me(
        user_id=user_id, tenant_id=tenant_id, status=observation_status,
        subject=subject, identifier=identifier, limit=params.limit, offset=params.offset,
        sort=params.sort, total_mode=params.total_mode,
    )
    return format_paginated_response(
        [observation_service._to_fhir(o) for o in items],
        [observation_service._to_plain(o) for o in items],
        total, params.limit, params.offset, request,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{observation_id}",
    operation_id="get_observation_by_id",
    summary="Retrieve an Observation resource by public observation_id",
    description=(
        "Loaded via `resolve_observation()` — a plain load-by-public-ID lookup with no "
        "ownership check (default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_observation(
    request: Request,
    observation: ObservationModel = Depends(resolve_observation),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info(
        "Retrieve an Observation resource by public observation_id",
        extra={"event": "route.get_observation_by_id", "observation_id": observation.observation_id},
    )
    return format_response(
        observation_service._to_fhir(observation),
        observation_service._to_plain(observation),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{observation_id}",
    operation_id="patch_observation",
    summary="Update an Observation resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (even `[]`) atomically replaces the corresponding rows; "
        "omitted lists are left untouched. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_observation(
    payload: ObservationPatchSchema,
    request: Request,
    observation_id: int = Path(..., ge=1, description="Public observation identifier."),
    _existing: ObservationModel = Depends(resolve_observation),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info("Update an Observation resource", extra={"event": "route.patch_observation", "observation_id": observation_id})
    log_payload(logger, "observation.patch.payload", payload)
    updated = await observation_service.patch_observation(observation_id, payload)
    return format_response(
        observation_service._to_fhir(updated),
        observation_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_observations",
    summary="List all Observation resources",
    description=(
        "Returns a paginated list of Observation resources, matching a subset of the "
        "search parameters documented at https://www.hl7.org/fhir/R4/observation.html#search. "
        "Filter by `status`, `subject` (exact), `identifier` (exact business-identifier "
        "value), plus `tenant_id`/`user_id` as explicit, gateway-forwarded query filters. "
        "Sort with `sort` (e.g. `-issued`); set `total_mode=none` to skip the COUNT(*) on "
        "large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_observations(
    request: Request,
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID filter."),
    user_id: str | None = Query(None, description="Gateway-forwarded end-user ID filter."),
    observation_status: ObservationStatus | None = Query(
        None, alias="status", description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown."
    ),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info("List all Observation resources", extra={"event": "route.list_observations"})
    items, total = await observation_service.list_observations(
        tenant_id=tenant_id, user_id=user_id, status=observation_status,
        subject=subject, identifier=identifier, limit=params.limit, offset=params.offset,
        sort=params.sort, total_mode=params.total_mode,
    )
    return format_paginated_response(
        [observation_service._to_fhir(o) for o in items],
        [observation_service._to_plain(o) for o in items],
        total, params.limit, params.offset, request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_observation",
    summary="Delete an Observation resource",
    description="Permanently deletes the Observation and all associated sub-resources. Returns 204 on success.",
    responses={**_ERR_NOT_FOUND},
)
async def delete_observation(
    observation_id: int = Path(..., ge=1, description="Public observation identifier."),
    _existing: ObservationModel = Depends(resolve_observation),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info("Delete an Observation resource", extra={"event": "route.delete_observation", "observation_id": observation_id})
    await observation_service.delete_observation(observation_id)
