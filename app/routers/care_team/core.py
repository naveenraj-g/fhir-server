from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.care_team import get_care_team_service
from app.schemas.care_team import (
    CareTeamCreateSchema,
    CareTeamPatchSchema,
)
from app.services.care_team import CareTeamService

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
    operation_id="create_care_team",
    summary="Create a new CareTeam resource",
    description=(
        "The Care Team includes all the people and organizations who plan to participate "
        "in the coordination and delivery of care for a patient. "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_care_team(
    payload: CareTeamCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_team", "create")),
    care_team_service: CareTeamService = Depends(get_care_team_service),
):
    logger.info(
        "Create a new CareTeam resource",
        extra={"event": "route.create_care_team"},
    )
    log_payload(logger, "care_team.create.payload", payload)
    ct = await care_team_service.create_care_team(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        care_team_service._to_fhir(ct),
        care_team_service._to_plain(ct),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{care_team_id}",
    operation_id="get_care_team",
    summary="Get a CareTeam resource by ID",
    description=(
        "Returns the full CareTeam resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_care_team(
    request: Request,
    care_team_id: int = Path(
        ..., ge=1, description="Public care_team identifier."
    ),
    actor: AuthUser = Depends(require_permission("care_team", "read")),
    care_team_service: CareTeamService = Depends(get_care_team_service),
):
    logger.info(
        "Get a CareTeam resource by ID",
        extra={"event": "route.get_care_team", "care_team_id": care_team_id},
    )
    ct = await care_team_service.get_care_team_scoped(
        care_team_id, actor.org_id
    )
    return format_response(
        care_team_service._to_fhir(ct),
        care_team_service._to_plain(ct),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{care_team_id}",
    operation_id="patch_care_team",
    summary="Update a CareTeam resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_care_team(
    payload: CareTeamPatchSchema,
    request: Request,
    care_team_id: int = Path(
        ..., ge=1, description="Public care_team identifier."
    ),
    actor: AuthUser = Depends(require_permission("care_team", "update")),
    care_team_service: CareTeamService = Depends(get_care_team_service),
):
    logger.info(
        "Update a CareTeam resource",
        extra={
            "event": "route.patch_care_team",
            "care_team_id": care_team_id,
        },
    )
    log_payload(logger, "care_team.patch.payload", payload)
    updated = await care_team_service.patch_care_team(
        care_team_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        care_team_service._to_fhir(updated),
        care_team_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_care_teams",
    summary="List all CareTeam resources",
    description=(
        "Returns a paginated list of CareTeam resources. Filter by status, "
        "name, category, subject, encounter, participant, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_care_teams(
    request: Request,
    actor: AuthUser = Depends(require_permission("care_team", "read")),
    status: str | None = Query(
        None, description="Status code (e.g. proposed, active, suspended, inactive, entered-in-error)."
    ),
    name: str | None = Query(None, description="Care team name."),
    category: str | None = Query(None, description="Category code."),
    subject: str | None = Query(None, description="Subject reference (e.g. Patient/10001 or Group/...)."),
    encounter: str | None = Query(None, description="Encounter reference (e.g. Encounter/20001)."),
    participant: str | None = Query(None, description="Participant member reference (e.g. Practitioner/30001)."),
    identifier: str | None = Query(None, description="Business identifier value."),
    list_params: ListParams = Depends(),
    care_team_service: CareTeamService = Depends(get_care_team_service),
):
    logger.info(
        "List CareTeam resources",
        extra={"event": "route.list_care_teams", "org_id": actor.org_id},
    )
    care_teams, total = await care_team_service.list_care_teams(
        org_id=actor.org_id,
        status=status,
        name=name,
        category=category,
        subject=subject,
        encounter=encounter,
        participant=participant,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [care_team_service._to_fhir(ct) for ct in care_teams],
        [care_team_service._to_plain(ct) for ct in care_teams],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{care_team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_care_team",
    summary="Delete a CareTeam resource",
    description=(
        "Permanently deletes the CareTeam and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_care_team(
    care_team_id: int = Path(
        ..., ge=1, description="Public care_team identifier."
    ),
    actor: AuthUser = Depends(require_permission("care_team", "delete")),
    care_team_service: CareTeamService = Depends(get_care_team_service),
):
    logger.info(
        "Delete a CareTeam resource",
        extra={
            "event": "route.delete_care_team",
            "care_team_id": care_team_id,
        },
    )
    await care_team_service.delete_care_team(
        care_team_id, org_id=actor.org_id
    )
