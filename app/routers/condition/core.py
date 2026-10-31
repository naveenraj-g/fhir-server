from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.condition import get_condition_service
from app.schemas.condition import ConditionCreateSchema, ConditionPatchSchema
from app.services.condition import ConditionService

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
    operation_id="create_condition",
    summary="Create a new Condition resource",
    description=(
        "Detailed information about conditions, problems or diagnoses. "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_condition(
    payload: ConditionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("condition", "create")),
    condition_service: ConditionService = Depends(get_condition_service),
):
    logger.info("Create a new Condition resource", extra={"event": "route.create_condition"})
    log_payload(logger, "condition.create.payload", payload)
    condition = await condition_service.create_condition(payload, actor.org_id, actor.sub)
    return format_response(
        condition_service._to_fhir(condition),
        condition_service._to_plain(condition),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{condition_id}",
    operation_id="get_condition_by_id",
    summary="Retrieve a Condition resource by public condition_id",
    description=(
        "Scoped to the caller's own org — get_condition_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_condition(
    request: Request,
    condition_id: int = Path(..., ge=1, description="Public condition identifier."),
    actor: AuthUser = Depends(require_permission("condition", "read")),
    condition_service: ConditionService = Depends(get_condition_service),
):
    logger.info(
        "Retrieve a Condition resource by public condition_id",
        extra={"event": "route.get_condition_by_id", "condition_id": condition_id},
    )
    condition = await condition_service.get_condition_scoped(condition_id, actor.org_id)
    return format_response(
        condition_service._to_fhir(condition),
        condition_service._to_plain(condition),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{condition_id}",
    operation_id="patch_condition",
    summary="Update a Condition resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_condition(
    payload: ConditionPatchSchema,
    request: Request,
    condition_id: int = Path(..., ge=1, description="Public condition identifier."),
    actor: AuthUser = Depends(require_permission("condition", "update")),
    condition_service: ConditionService = Depends(get_condition_service),
):
    logger.info(
        "Update a Condition resource",
        extra={"event": "route.patch_condition", "condition_id": condition_id},
    )
    log_payload(logger, "condition.patch.payload", payload)
    updated = await condition_service.patch_condition(
        condition_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        condition_service._to_fhir(updated),
        condition_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_conditions",
    summary="List all Condition resources",
    description=(
        "Returns a paginated list of Condition resources. Filter by clinical_status, "
        "verification_status, category, severity, code, subject, encounter, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_conditions(
    request: Request,
    actor: AuthUser = Depends(require_permission("condition", "read")),
    clinical_status: str | None = Query(None, description="Clinical status code, e.g. active, resolved."),
    verification_status: str | None = Query(None, description="Verification status code, e.g. confirmed."),
    category: str | None = Query(None, description="Category code, e.g. problem-list-item."),
    severity: str | None = Query(None, description="Severity code."),
    code: str | None = Query(None, description="Condition code."),
    subject: str | None = Query(None, description="Exact match on subject reference string."),
    encounter: str | None = Query(None, description="Exact match on encounter reference string."),
    identifier: str | None = Query(None, description="Exact match on business identifier value."),
    params: ListParams = Depends(),
    condition_service: ConditionService = Depends(get_condition_service),
):
    logger.info("List all Condition resources", extra={"event": "route.list_conditions"})
    items, total = await condition_service.list_conditions(
        org_id=actor.org_id,
        clinical_status=clinical_status,
        verification_status=verification_status,
        category=category,
        severity=severity,
        code=code,
        subject=subject,
        encounter=encounter,
        identifier=identifier,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [condition_service._to_fhir(c) for c in items],
        [condition_service._to_plain(c) for c in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_condition",
    summary="Delete a Condition resource",
    description=(
        "Permanently deletes the Condition and all associated sub-resources. Scoped "
        "to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_condition(
    condition_id: int = Path(..., ge=1, description="Public condition identifier."),
    actor: AuthUser = Depends(require_permission("condition", "delete")),
    condition_service: ConditionService = Depends(get_condition_service),
):
    logger.info(
        "Delete a Condition resource",
        extra={"event": "route.delete_condition", "condition_id": condition_id},
    )
    await condition_service.delete_condition(condition_id, org_id=actor.org_id)
