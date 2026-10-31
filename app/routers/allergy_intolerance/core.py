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
from app.di.dependencies.allergy_intolerance import get_allergy_intolerance_service
from app.schemas.allergy_intolerance import (
    AllergyIntoleranceCreateSchema,
    AllergyIntolerancePatchSchema,
)
from app.services.allergy_intolerance import AllergyIntoleranceService

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
    operation_id="create_allergy_intolerance",
    summary="Create a new AllergyIntolerance resource",
    description=(
        "Risk of harmful or undesirable, physiological response which is unique to an individual "
        "and results from exposure to a substance. Accepts the full nested payload atomically in "
        "one DB transaction. `tenant_id`/`created_by` come from the verified JWT "
        "(`actor.org_id`/`actor.sub`) — an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_allergy_intolerance(
    payload: AllergyIntoleranceCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "create")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    logger.info(
        "Create a new AllergyIntolerance resource",
        extra={"event": "route.create_allergy_intolerance"},
    )
    log_payload(logger, "allergy_intolerance.create.payload", payload)
    model = await allergy_intolerance_service.create_allergy_intolerance(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        allergy_intolerance_service._to_fhir(model),
        allergy_intolerance_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{allergy_intolerance_id}",
    operation_id="get_allergy_intolerance",
    summary="Get an AllergyIntolerance resource by ID",
    description=(
        "Returns the full AllergyIntolerance resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_allergy_intolerance(
    request: Request,
    allergy_intolerance_id: int = Path(
        ..., ge=1, description="Public AllergyIntolerance identifier."
    ),
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "read")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    logger.info(
        "Get an AllergyIntolerance resource by ID",
        extra={
            "event": "route.get_allergy_intolerance",
            "allergy_intolerance_id": allergy_intolerance_id,
        },
    )
    model = await allergy_intolerance_service.get_allergy_intolerance_scoped(
        allergy_intolerance_id, actor.org_id
    )
    return format_response(
        allergy_intolerance_service._to_fhir(model),
        allergy_intolerance_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{allergy_intolerance_id}",
    operation_id="patch_allergy_intolerance",
    summary="Update an AllergyIntolerance resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_allergy_intolerance(
    payload: AllergyIntolerancePatchSchema,
    request: Request,
    allergy_intolerance_id: int = Path(
        ..., ge=1, description="Public AllergyIntolerance identifier."
    ),
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "update")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    logger.info(
        "Update an AllergyIntolerance resource",
        extra={
            "event": "route.patch_allergy_intolerance",
            "allergy_intolerance_id": allergy_intolerance_id,
        },
    )
    log_payload(logger, "allergy_intolerance.patch.payload", payload)
    updated = await allergy_intolerance_service.patch_allergy_intolerance(
        allergy_intolerance_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        allergy_intolerance_service._to_fhir(updated),
        allergy_intolerance_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_allergy_intolerances",
    summary="List all AllergyIntolerance resources",
    description=(
        "Returns a paginated list of AllergyIntolerance resources. Filter by clinical-status, "
        "verification-status, type, category, criticality, code, patient, severity, date, "
        "recorder, asserter, identifier. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_allergy_intolerances(
    request: Request,
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "read")),
    clinical_status: str | None = Query(
        None,
        description="active | recurrence | relapse | inactive | remission | resolved.",
    ),
    verification_status: str | None = Query(
        None,
        description="unconfirmed | presumed | confirmed | refuted | entered-in-error.",
    ),
    type: str | None = Query(
        None, description="allergy | intolerance."
    ),
    category: str | None = Query(
        None, description="food | medication | environment | biologic."
    ),
    criticality: str | None = Query(
        None, description="low | high | unable-to-assess."
    ),
    code: str | None = Query(
        None, description="Code that identifies the allergy or intolerance."
    ),
    patient: str | None = Query(
        None, description="Who the sensitivity is for (Patient reference)."
    ),
    severity: str | None = Query(
        None, description="mild | moderate | severe (reaction severity)."
    ),
    date_val: date | None = Query(
        None, description="Exact date resource was recorded."
    ),
    date_from: datetime | None = Query(
        None, description="Recorded date range start."
    ),
    date_to: datetime | None = Query(
        None, description="Recorded date range end."
    ),
    recorder: str | None = Query(
        None, description="Who recorded the sensitivity (reference)."
    ),
    asserter: str | None = Query(
        None, description="Source of the information about the allergy (reference)."
    ),
    identifier: str | None = Query(
        None, description="Business identifier value."
    ),
    list_params: ListParams = Depends(),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    logger.info(
        "List AllergyIntolerance resources",
        extra={"event": "route.list_allergy_intolerances", "org_id": actor.org_id},
    )
    items, total = await allergy_intolerance_service.list_allergy_intolerances(
        org_id=actor.org_id,
        clinical_status=clinical_status,
        verification_status=verification_status,
        type=type,
        category=category,
        criticality=criticality,
        code=code,
        patient=patient,
        severity=severity,
        date_val=date_val,
        date_from=date_from,
        date_to=date_to,
        recorder=recorder,
        asserter=asserter,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [allergy_intolerance_service._to_fhir(m) for m in items],
        [allergy_intolerance_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{allergy_intolerance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_allergy_intolerance",
    summary="Delete an AllergyIntolerance resource",
    description=(
        "Permanently deletes the AllergyIntolerance and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_allergy_intolerance(
    allergy_intolerance_id: int = Path(
        ..., ge=1, description="Public AllergyIntolerance identifier."
    ),
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "delete")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    logger.info(
        "Delete an AllergyIntolerance resource",
        extra={
            "event": "route.delete_allergy_intolerance",
            "allergy_intolerance_id": allergy_intolerance_id,
        },
    )
    await allergy_intolerance_service.delete_allergy_intolerance(
        allergy_intolerance_id, org_id=actor.org_id
    )
