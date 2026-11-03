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
from app.di.dependencies.immunization_evaluation import (
    get_immunization_evaluation_service,
)
from app.schemas.immunization_evaluation import (
    ImmunizationEvaluationCreateSchema,
    ImmunizationEvaluationPatchSchema,
)
from app.services.immunization_evaluation import ImmunizationEvaluationService

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
    operation_id="create_immunization_evaluation",
    summary="Create a new ImmunizationEvaluation resource",
    description=(
        "Describes a comparison of an immunization event against published "
        "recommendations to determine if the administration is 'valid' in relation "
        "to a specific protocol. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_immunization_evaluation(
    payload: ImmunizationEvaluationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "create")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(
        get_immunization_evaluation_service
    ),
):
    logger.info(
        "Create a new ImmunizationEvaluation resource",
        extra={"event": "route.create_immunization_evaluation", "org_id": actor.org_id},
    )
    log_payload(logger, "immunization_evaluation.create.payload", payload)
    model = await immunization_evaluation_service.create_immunization_evaluation(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        immunization_evaluation_service._to_fhir(model),
        immunization_evaluation_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{immunization_evaluation_id}",
    operation_id="get_immunization_evaluation",
    summary="Get an ImmunizationEvaluation resource by ID",
    description=(
        "Returns the complete ImmunizationEvaluation representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_immunization_evaluation(
    request: Request,
    immunization_evaluation_id: int = Path(
        ..., ge=1, description="Public ImmunizationEvaluation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "read")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(
        get_immunization_evaluation_service
    ),
):
    logger.info(
        "Get an ImmunizationEvaluation resource by ID",
        extra={
            "event": "route.get_immunization_evaluation",
            "immunization_evaluation_id": immunization_evaluation_id,
        },
    )
    model = await immunization_evaluation_service.get_immunization_evaluation_scoped(
        immunization_evaluation_id, actor.org_id
    )
    return format_response(
        immunization_evaluation_service._to_fhir(model),
        immunization_evaluation_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{immunization_evaluation_id}",
    operation_id="patch_immunization_evaluation",
    summary="Update an ImmunizationEvaluation resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_immunization_evaluation(
    payload: ImmunizationEvaluationPatchSchema,
    request: Request,
    immunization_evaluation_id: int = Path(
        ..., ge=1, description="Public ImmunizationEvaluation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "update")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(
        get_immunization_evaluation_service
    ),
):
    logger.info(
        "Update an ImmunizationEvaluation resource",
        extra={
            "event": "route.patch_immunization_evaluation",
            "immunization_evaluation_id": immunization_evaluation_id,
        },
    )
    log_payload(logger, "immunization_evaluation.patch.payload", payload)
    model = await immunization_evaluation_service.patch_immunization_evaluation(
        immunization_evaluation_id, payload, updated_by=actor.sub, org_id=actor.org_id
    )
    return format_response(
        immunization_evaluation_service._to_fhir(model),
        immunization_evaluation_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_immunization_evaluations",
    summary="List ImmunizationEvaluation resources",
    description=(
        "Search and filter ImmunizationEvaluation resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_immunization_evaluations(
    request: Request,
    status_filter: str | None = Query(
        None,
        alias="status",
        description="completed | entered-in-error",
    ),
    patient: str | None = Query(
        None,
        description="Patient for whom evaluation was done (Reference(Patient), e.g. 'Patient/10001').",
    ),
    date_val: date | datetime | str | None = Query(
        None,
        alias="date",
        description="Date evaluation was performed.",
    ),
    authority: str | None = Query(
        None,
        description="Who is responsible for protocol (Reference(Organization), e.g. 'Organization/190001').",
    ),
    immunization_event: str | None = Query(
        None,
        alias="immunization-event",
        description="Immunization event evaluated (Reference(Immunization), e.g. 'Immunization/330001').",
    ),
    identifier: str | None = Query(
        None,
        description="Business identifier (system|value or token).",
    ),
    target_disease: str | None = Query(
        None,
        alias="target-disease",
        description="Evaluation target disease code.",
    ),
    dose_status: str | None = Query(
        None,
        alias="dose-status",
        description="Dose status code (valid | notvalid).",
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "read")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(
        get_immunization_evaluation_service
    ),
):
    logger.info(
        "List ImmunizationEvaluation resources",
        extra={"event": "route.list_immunization_evaluations", "org_id": actor.org_id},
    )
    items, total = await immunization_evaluation_service.list_immunization_evaluations(
        org_id=actor.org_id,
        status=status_filter,
        patient=patient,
        date_val=date_val,
        authority=authority,
        immunization_event=immunization_event,
        identifier=identifier,
        target_disease=target_disease,
        dose_status=dose_status,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    return format_paginated_response(
        [immunization_evaluation_service._to_fhir(m) for m in items],
        [immunization_evaluation_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{immunization_evaluation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_immunization_evaluation",
    summary="Delete an ImmunizationEvaluation resource",
    description=(
        "Deletes an ImmunizationEvaluation and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "ImmunizationEvaluation deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_immunization_evaluation(
    immunization_evaluation_id: int = Path(
        ..., ge=1, description="Public ImmunizationEvaluation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "delete")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(
        get_immunization_evaluation_service
    ),
):
    logger.info(
        "Delete an ImmunizationEvaluation resource",
        extra={
            "event": "route.delete_immunization_evaluation",
            "immunization_evaluation_id": immunization_evaluation_id,
        },
    )
    await immunization_evaluation_service.delete_immunization_evaluation(
        immunization_evaluation_id, org_id=actor.org_id
    )
    return None
