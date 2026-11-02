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
from app.di.dependencies.family_member_history import get_family_member_history_service
from app.schemas.family_member_history import (
    FamilyMemberHistoryCreateSchema,
    FamilyMemberHistoryPatchSchema,
)
from app.services.family_member_history import FamilyMemberHistoryService

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
    operation_id="create_family_member_history",
    summary="Create a new FamilyMemberHistory resource",
    description=(
        "Significant health events and conditions for a person related to the patient. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_family_member_history(
    payload: FamilyMemberHistoryCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("family_member_history", "create")),
    family_member_history_service: FamilyMemberHistoryService = Depends(
        get_family_member_history_service
    ),
):
    logger.info(
        "Create a new FamilyMemberHistory resource",
        extra={"event": "route.create_family_member_history", "org_id": actor.org_id},
    )
    log_payload(logger, "family_member_history.create.payload", payload)
    model = await family_member_history_service.create_family_member_history(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        family_member_history_service._to_fhir(model),
        family_member_history_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{family_member_history_id}",
    operation_id="get_family_member_history",
    summary="Get a FamilyMemberHistory resource by ID",
    description=(
        "Returns the complete FamilyMemberHistory representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_family_member_history(
    request: Request,
    family_member_history_id: int = Path(
        ..., ge=1, description="Public FamilyMemberHistory identifier."
    ),
    actor: AuthUser = Depends(require_permission("family_member_history", "read")),
    family_member_history_service: FamilyMemberHistoryService = Depends(
        get_family_member_history_service
    ),
):
    logger.info(
        "Get a FamilyMemberHistory resource by ID",
        extra={
            "event": "route.get_family_member_history",
            "family_member_history_id": family_member_history_id,
        },
    )
    model = await family_member_history_service.get_family_member_history_scoped(
        family_member_history_id, actor.org_id
    )
    return format_response(
        family_member_history_service._to_fhir(model),
        family_member_history_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{family_member_history_id}",
    operation_id="patch_family_member_history",
    summary="Update a FamilyMemberHistory resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_family_member_history(
    payload: FamilyMemberHistoryPatchSchema,
    request: Request,
    family_member_history_id: int = Path(
        ..., ge=1, description="Public FamilyMemberHistory identifier."
    ),
    actor: AuthUser = Depends(require_permission("family_member_history", "update")),
    family_member_history_service: FamilyMemberHistoryService = Depends(
        get_family_member_history_service
    ),
):
    logger.info(
        "Update a FamilyMemberHistory resource",
        extra={
            "event": "route.patch_family_member_history",
            "family_member_history_id": family_member_history_id,
        },
    )
    log_payload(logger, "family_member_history.patch.payload", payload)
    updated = await family_member_history_service.patch_family_member_history(
        family_member_history_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        family_member_history_service._to_fhir(updated),
        family_member_history_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_family_member_histories",
    summary="List all FamilyMemberHistory resources",
    description=(
        "Returns a paginated list of FamilyMemberHistory resources. Filter by status, "
        "patient, date, relationship, sex, code, identifier, instantiates. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_family_member_histories(
    request: Request,
    actor: AuthUser = Depends(require_permission("family_member_history", "read")),
    history_status: str | None = Query(
        None,
        alias="status",
        description="partial | completed | entered-in-error | health-unknown.",
    ),
    patient: str | None = Query(
        None, description="Patient history is about (Patient reference)."
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
    relationship: str | None = Query(
        None, description="Relationship to the subject (code or text)."
    ),
    sex: str | None = Query(
        None, description="Sex of family member (code or text)."
    ),
    code: str | None = Query(
        None, description="Condition code of family member."
    ),
    identifier: str | None = Query(
        None, description="Business identifier value."
    ),
    instantiates: str | None = Query(
        None, description="Canonical or URI protocol instantiated."
    ),
    list_params: ListParams = Depends(),
    family_member_history_service: FamilyMemberHistoryService = Depends(
        get_family_member_history_service
    ),
):
    logger.info(
        "List FamilyMemberHistory resources",
        extra={"event": "route.list_family_member_histories", "org_id": actor.org_id},
    )
    items, total = await family_member_history_service.list_family_member_histories(
        org_id=actor.org_id,
        status=history_status,
        patient=patient,
        date_val=date_val,
        date_from=date_from,
        date_to=date_to,
        relationship=relationship,
        sex=sex,
        code=code,
        identifier=identifier,
        instantiates=instantiates,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [family_member_history_service._to_fhir(m) for m in items],
        [family_member_history_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{family_member_history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_family_member_history",
    summary="Delete a FamilyMemberHistory resource",
    description=(
        "Deletes a FamilyMemberHistory and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "FamilyMemberHistory deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_family_member_history(
    family_member_history_id: int = Path(
        ..., ge=1, description="Public FamilyMemberHistory identifier."
    ),
    actor: AuthUser = Depends(require_permission("family_member_history", "delete")),
    family_member_history_service: FamilyMemberHistoryService = Depends(
        get_family_member_history_service
    ),
):
    logger.info(
        "Delete a FamilyMemberHistory resource",
        extra={
            "event": "route.delete_family_member_history",
            "family_member_history_id": family_member_history_id,
        },
    )
    await family_member_history_service.delete_family_member_history(
        family_member_history_id, org_id=actor.org_id
    )
    return None
