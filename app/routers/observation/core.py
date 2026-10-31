from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.observation import get_observation_service
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
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_observation(
    payload: ObservationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("observation", "create")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info("Create a new Observation resource", extra={"event": "route.create_observation"})
    log_payload(logger, "observation.create.payload", payload)
    observation = await observation_service.create_observation(payload, actor.org_id, actor.sub)
    return format_response(
        observation_service._to_fhir(observation),
        observation_service._to_plain(observation),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{observation_id}",
    operation_id="get_observation_by_id",
    summary="Retrieve an Observation resource by public observation_id",
    description=(
        "Scoped to the caller's own org — get_observation_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_observation(
    request: Request,
    observation_id: int = Path(..., ge=1, description="Public observation identifier."),
    actor: AuthUser = Depends(require_permission("observation", "read")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info(
        "Retrieve an Observation resource by public observation_id",
        extra={"event": "route.get_observation_by_id", "observation_id": observation_id},
    )
    observation = await observation_service.get_observation_scoped(observation_id, actor.org_id)
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
        "omitted lists are left untouched. Scoped to the caller's own org — "
        "patch_observation() raises NotFoundError (404, not 403) if actor.org_id "
        "doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_observation(
    payload: ObservationPatchSchema,
    request: Request,
    observation_id: int = Path(..., ge=1, description="Public observation identifier."),
    actor: AuthUser = Depends(require_permission("observation", "update")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info("Update an Observation resource", extra={"event": "route.patch_observation", "observation_id": observation_id})
    log_payload(logger, "observation.patch.payload", payload)
    updated = await observation_service.patch_observation(
        observation_id, payload, actor.sub, org_id=actor.org_id
    )
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
        "value). Always scoped to the caller's own org (from the verified token) — "
        "`org_id` is not a client-suppliable filter. Sort with `sort` (e.g. `-issued`); "
        "set `total_mode=none` to skip the COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_observations(
    request: Request,
    actor: AuthUser = Depends(require_permission("observation", "read")),
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
        org_id=actor.org_id, status=observation_status,
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
    description=(
        "Permanently deletes the Observation and all associated sub-resources. Scoped "
        "to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_observation(
    observation_id: int = Path(..., ge=1, description="Public observation identifier."),
    actor: AuthUser = Depends(require_permission("observation", "delete")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info("Delete an Observation resource", extra={"event": "route.delete_observation", "observation_id": observation_id})
    await observation_service.delete_observation(observation_id, org_id=actor.org_id)
