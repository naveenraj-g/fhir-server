from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.episode_of_care import get_episode_of_care_service
from app.schemas.episode_of_care import (
    EpisodeOfCareCreateSchema,
    EpisodeOfCarePatchSchema,
)
from app.services.episode_of_care import EpisodeOfCareService

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
    operation_id="create_episode_of_care",
    summary="Create a new EpisodeOfCare resource",
    description=(
        "An association between a patient and an organization / healthcare provider(s) "
        "during which time encounters may occur. "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_episode_of_care(
    payload: EpisodeOfCareCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("episode_of_care", "create")),
    episode_of_care_service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    logger.info(
        "Create a new EpisodeOfCare resource",
        extra={"event": "route.create_episode_of_care"},
    )
    log_payload(logger, "episode_of_care.create.payload", payload)
    eoc = await episode_of_care_service.create_episode_of_care(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        episode_of_care_service._to_fhir(eoc),
        episode_of_care_service._to_plain(eoc),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{episode_of_care_id}",
    operation_id="get_episode_of_care",
    summary="Get an EpisodeOfCare resource by ID",
    description=(
        "Returns the full EpisodeOfCare resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_episode_of_care(
    request: Request,
    episode_of_care_id: int = Path(
        ..., ge=1, description="Public episode_of_care identifier."
    ),
    actor: AuthUser = Depends(require_permission("episode_of_care", "read")),
    episode_of_care_service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    logger.info(
        "Get an EpisodeOfCare resource by ID",
        extra={"event": "route.get_episode_of_care", "episode_of_care_id": episode_of_care_id},
    )
    eoc = await episode_of_care_service.get_episode_of_care_scoped(
        episode_of_care_id, actor.org_id
    )
    return format_response(
        episode_of_care_service._to_fhir(eoc),
        episode_of_care_service._to_plain(eoc),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{episode_of_care_id}",
    operation_id="patch_episode_of_care",
    summary="Update an EpisodeOfCare resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_episode_of_care(
    payload: EpisodeOfCarePatchSchema,
    request: Request,
    episode_of_care_id: int = Path(
        ..., ge=1, description="Public episode_of_care identifier."
    ),
    actor: AuthUser = Depends(require_permission("episode_of_care", "update")),
    episode_of_care_service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    logger.info(
        "Update an EpisodeOfCare resource",
        extra={
            "event": "route.patch_episode_of_care",
            "episode_of_care_id": episode_of_care_id,
        },
    )
    log_payload(logger, "episode_of_care.patch.payload", payload)
    updated = await episode_of_care_service.patch_episode_of_care(
        episode_of_care_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        episode_of_care_service._to_fhir(updated),
        episode_of_care_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_episodes_of_care",
    summary="List all EpisodeOfCare resources",
    description=(
        "Returns a paginated list of EpisodeOfCare resources. Filter by status, "
        "patient, type, care_manager, organization, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_episodes_of_care(
    request: Request,
    actor: AuthUser = Depends(require_permission("episode_of_care", "read")),
    status: str | None = Query(
        None, description="Status code (e.g. planned, waitlist, active, onhold, finished, cancelled, entered-in-error)."
    ),
    patient: str | None = Query(None, description="Patient reference (e.g. Patient/10001)."),
    type: str | None = Query(None, description="Type code."),
    care_manager: str | None = Query(None, description="Care manager reference (e.g. Practitioner/30001 or PractitionerRole/140001)."),
    organization: str | None = Query(None, description="Managing organization reference (e.g. Organization/190001)."),
    identifier: str | None = Query(None, description="Business identifier value."),
    list_params: ListParams = Depends(),
    episode_of_care_service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    logger.info(
        "List EpisodeOfCare resources",
        extra={"event": "route.list_episodes_of_care", "org_id": actor.org_id},
    )
    episodes, total = await episode_of_care_service.list_episodes_of_care(
        org_id=actor.org_id,
        status=status,
        patient=patient,
        type=type,
        care_manager=care_manager,
        organization=organization,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [episode_of_care_service._to_fhir(e) for e in episodes],
        [episode_of_care_service._to_plain(e) for e in episodes],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{episode_of_care_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_episode_of_care",
    summary="Delete an EpisodeOfCare resource",
    description=(
        "Permanently deletes the EpisodeOfCare and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_episode_of_care(
    episode_of_care_id: int = Path(
        ..., ge=1, description="Public episode_of_care identifier."
    ),
    actor: AuthUser = Depends(require_permission("episode_of_care", "delete")),
    episode_of_care_service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    logger.info(
        "Delete an EpisodeOfCare resource",
        extra={
            "event": "route.delete_episode_of_care",
            "episode_of_care_id": episode_of_care_id,
        },
    )
    await episode_of_care_service.delete_episode_of_care(
        episode_of_care_id, org_id=actor.org_id
    )
