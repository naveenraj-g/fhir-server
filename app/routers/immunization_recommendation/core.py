from datetime import date, datetime

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.immunization_recommendation import get_immunization_recommendation_service
from app.schemas.immunization_recommendation import (
    ImmunizationRecommendationCreateSchema,
    ImmunizationRecommendationPatchSchema,
)
from app.services.immunization_recommendation import ImmunizationRecommendationService

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
    operation_id="create_immunization_recommendation",
    summary="Create a new ImmunizationRecommendation resource",
    description=(
        "A patient's point-in-time set of recommendations according to a published schedule. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_immunization_recommendation(
    payload: ImmunizationRecommendationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization_recommendation", "create")),
    immunization_recommendation_service: ImmunizationRecommendationService = Depends(
        get_immunization_recommendation_service
    ),
):
    logger.info(
        "Create a new ImmunizationRecommendation resource",
        extra={"event": "route.create_immunization_recommendation", "org_id": actor.org_id},
    )
    log_payload(logger, "immunization_recommendation.create.payload", payload)
    model = await immunization_recommendation_service.create_immunization_recommendation(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        immunization_recommendation_service._to_fhir(model),
        immunization_recommendation_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{immunization_recommendation_id}",
    operation_id="get_immunization_recommendation",
    summary="Get an ImmunizationRecommendation resource by ID",
    description=(
        "Returns the complete ImmunizationRecommendation representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_immunization_recommendation(
    request: Request,
    immunization_recommendation_id: int = Path(
        ..., ge=1, description="Public ImmunizationRecommendation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_recommendation", "read")),
    immunization_recommendation_service: ImmunizationRecommendationService = Depends(
        get_immunization_recommendation_service
    ),
):
    logger.info(
        "Get an ImmunizationRecommendation resource by ID",
        extra={
            "event": "route.get_immunization_recommendation",
            "immunization_recommendation_id": immunization_recommendation_id,
        },
    )
    model = await immunization_recommendation_service.get_immunization_recommendation_scoped(
        immunization_recommendation_id, actor.org_id
    )
    return format_response(
        immunization_recommendation_service._to_fhir(model),
        immunization_recommendation_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{immunization_recommendation_id}",
    operation_id="patch_immunization_recommendation",
    summary="Update an ImmunizationRecommendation resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_immunization_recommendation(
    payload: ImmunizationRecommendationPatchSchema,
    request: Request,
    immunization_recommendation_id: int = Path(
        ..., ge=1, description="Public ImmunizationRecommendation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_recommendation", "update")),
    immunization_recommendation_service: ImmunizationRecommendationService = Depends(
        get_immunization_recommendation_service
    ),
):
    logger.info(
        "Update an ImmunizationRecommendation resource",
        extra={
            "event": "route.patch_immunization_recommendation",
            "immunization_recommendation_id": immunization_recommendation_id,
        },
    )
    log_payload(logger, "immunization_recommendation.patch.payload", payload)
    updated = await immunization_recommendation_service.patch_immunization_recommendation(
        immunization_recommendation_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        immunization_recommendation_service._to_fhir(updated),
        immunization_recommendation_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_immunization_recommendations",
    summary="List all ImmunizationRecommendation resources",
    description=(
        "Returns a paginated list of ImmunizationRecommendation resources. Filter by patient, "
        "date, identifier. Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_immunization_recommendations(
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization_recommendation", "read")),
    patient: str | None = Query(
        None, description="Patient who this recommendation profile is for."
    ),
    date_val: date | None = Query(
        None, alias="date", description="Recommendation generation date."
    ),
    date_from: datetime | None = Query(
        None, description="Generation date range start."
    ),
    date_to: datetime | None = Query(
        None, description="Generation date range end."
    ),
    identifier: str | None = Query(
        None, description="Business identifier value."
    ),
    list_params: ListParams = Depends(),
    immunization_recommendation_service: ImmunizationRecommendationService = Depends(
        get_immunization_recommendation_service
    ),
):
    logger.info(
        "List ImmunizationRecommendation resources",
        extra={"event": "route.list_immunization_recommendations", "org_id": actor.org_id},
    )
    items, total = await immunization_recommendation_service.list_immunization_recommendations(
        org_id=actor.org_id,
        patient=patient,
        date_val=date_val,
        date_from=date_from,
        date_to=date_to,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [immunization_recommendation_service._to_fhir(m) for m in items],
        [immunization_recommendation_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{immunization_recommendation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_immunization_recommendation",
    summary="Delete an ImmunizationRecommendation resource",
    description=(
        "Deletes an ImmunizationRecommendation and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "ImmunizationRecommendation deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_immunization_recommendation(
    immunization_recommendation_id: int = Path(
        ..., ge=1, description="Public ImmunizationRecommendation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_recommendation", "delete")),
    immunization_recommendation_service: ImmunizationRecommendationService = Depends(
        get_immunization_recommendation_service
    ),
):
    logger.info(
        "Delete an ImmunizationRecommendation resource",
        extra={
            "event": "route.delete_immunization_recommendation",
            "immunization_recommendation_id": immunization_recommendation_id,
        },
    )
    await immunization_recommendation_service.delete_immunization_recommendation(
        immunization_recommendation_id, org_id=actor.org_id
    )
    return None
