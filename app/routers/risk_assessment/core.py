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
from app.di.dependencies.risk_assessment import get_risk_assessment_service
from app.schemas.risk_assessment import (
    RiskAssessmentCreateSchema,
    RiskAssessmentPatchSchema,
)
from app.services.risk_assessment import RiskAssessmentService

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
    operation_id="create_risk_assessment",
    summary="Create a new RiskAssessment resource",
    description=(
        "An assessment of the likely outcome(s) for a patient or other subject as well "
        "as the likelihood of each outcome. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_risk_assessment(
    payload: RiskAssessmentCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("risk_assessment", "create")),
    risk_assessment_service: RiskAssessmentService = Depends(
        get_risk_assessment_service
    ),
):
    logger.info(
        "Create a new RiskAssessment resource",
        extra={"event": "route.create_risk_assessment", "org_id": actor.org_id},
    )
    log_payload(logger, "risk_assessment.create.payload", payload)
    model = await risk_assessment_service.create_risk_assessment(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        risk_assessment_service._to_fhir(model),
        risk_assessment_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{risk_assessment_id}",
    operation_id="get_risk_assessment",
    summary="Get a RiskAssessment resource by ID",
    description=(
        "Returns the complete RiskAssessment representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_risk_assessment(
    request: Request,
    risk_assessment_id: int = Path(
        ..., ge=1, description="Public RiskAssessment identifier."
    ),
    actor: AuthUser = Depends(require_permission("risk_assessment", "read")),
    risk_assessment_service: RiskAssessmentService = Depends(
        get_risk_assessment_service
    ),
):
    logger.info(
        "Get a RiskAssessment resource by ID",
        extra={
            "event": "route.get_risk_assessment",
            "risk_assessment_id": risk_assessment_id,
        },
    )
    model = await risk_assessment_service.get_risk_assessment_scoped(
        risk_assessment_id, actor.org_id
    )
    return format_response(
        risk_assessment_service._to_fhir(model),
        risk_assessment_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{risk_assessment_id}",
    operation_id="patch_risk_assessment",
    summary="Update a RiskAssessment resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_risk_assessment(
    payload: RiskAssessmentPatchSchema,
    request: Request,
    risk_assessment_id: int = Path(
        ..., ge=1, description="Public RiskAssessment identifier."
    ),
    actor: AuthUser = Depends(require_permission("risk_assessment", "update")),
    risk_assessment_service: RiskAssessmentService = Depends(
        get_risk_assessment_service
    ),
):
    logger.info(
        "Update a RiskAssessment resource",
        extra={
            "event": "route.patch_risk_assessment",
            "risk_assessment_id": risk_assessment_id,
        },
    )
    log_payload(logger, "risk_assessment.patch.payload", payload)
    model = await risk_assessment_service.patch_risk_assessment(
        risk_assessment_id, payload, updated_by=actor.sub, org_id=actor.org_id
    )
    return format_response(
        risk_assessment_service._to_fhir(model),
        risk_assessment_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_risk_assessments",
    summary="List RiskAssessment resources",
    description=(
        "Search and filter RiskAssessment resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_risk_assessments(
    request: Request,
    risk_assessment_status: str | None = Query(
        None,
        alias="status",
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.",
    ),
    subject: str | None = Query(
        None, description="Who/what does assessment apply to? (e.g. 'Patient/10001')."
    ),
    condition: str | None = Query(
        None, description="Condition assessed (e.g. 'Condition/120001')."
    ),
    performer: str | None = Query(
        None, description="Who did assessment? (e.g. 'Practitioner/30001')."
    ),
    occurrence: date | datetime | str | None = Query(
        None, description="When was assessment made?"
    ),
    identifier: str | None = Query(
        None, description="Filter by business identifier system|value."
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("risk_assessment", "read")),
    risk_assessment_service: RiskAssessmentService = Depends(
        get_risk_assessment_service
    ),
):
    logger.info(
        "List RiskAssessment resources",
        extra={
            "event": "route.list_risk_assessments",
            "status": risk_assessment_status,
            "subject": subject,
            "condition": condition,
            "performer": performer,
            "occurrence": str(occurrence) if occurrence else None,
            "identifier": identifier,
            "limit": list_params.limit,
            "offset": list_params.offset,
        },
    )
    items, total = await risk_assessment_service.list_risk_assessments(
        org_id=actor.org_id,
        status=risk_assessment_status,
        subject=subject,
        condition=condition,
        performer=performer,
        occurrence=occurrence,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    return format_paginated_response(
        [risk_assessment_service._to_fhir(m) for m in items],
        [risk_assessment_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{risk_assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_risk_assessment",
    summary="Delete a RiskAssessment resource",
    description=(
        "Deletes a RiskAssessment and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "RiskAssessment deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_risk_assessment(
    risk_assessment_id: int = Path(
        ..., ge=1, description="Public RiskAssessment identifier."
    ),
    actor: AuthUser = Depends(require_permission("risk_assessment", "delete")),
    risk_assessment_service: RiskAssessmentService = Depends(
        get_risk_assessment_service
    ),
):
    logger.info(
        "Delete a RiskAssessment resource",
        extra={
            "event": "route.delete_risk_assessment",
            "risk_assessment_id": risk_assessment_id,
        },
    )
    await risk_assessment_service.delete_risk_assessment(
        risk_assessment_id, org_id=actor.org_id
    )
    return None
