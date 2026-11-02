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
from app.di.dependencies.detected_issue import get_detected_issue_service
from app.schemas.detected_issue import (
    DetectedIssueCreateSchema,
    DetectedIssuePatchSchema,
)
from app.services.detected_issue import DetectedIssueService

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
    operation_id="create_detected_issue",
    summary="Create a new DetectedIssue resource",
    description=(
        "Indicates an actual or potential clinical issue with or between one or more "
        "active or proposed clinical actions for a patient. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_detected_issue(
    payload: DetectedIssueCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("detected_issue", "create")),
    detected_issue_service: DetectedIssueService = Depends(
        get_detected_issue_service
    ),
):
    logger.info(
        "Create a new DetectedIssue resource",
        extra={"event": "route.create_detected_issue", "org_id": actor.org_id},
    )
    log_payload(logger, "detected_issue.create.payload", payload)
    model = await detected_issue_service.create_detected_issue(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        detected_issue_service._to_fhir(model),
        detected_issue_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{detected_issue_id}",
    operation_id="get_detected_issue",
    summary="Get a DetectedIssue resource by ID",
    description=(
        "Returns the complete DetectedIssue representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_detected_issue(
    request: Request,
    detected_issue_id: int = Path(
        ..., ge=1, description="Public DetectedIssue identifier."
    ),
    actor: AuthUser = Depends(require_permission("detected_issue", "read")),
    detected_issue_service: DetectedIssueService = Depends(
        get_detected_issue_service
    ),
):
    logger.info(
        "Get a DetectedIssue resource by ID",
        extra={
            "event": "route.get_detected_issue",
            "detected_issue_id": detected_issue_id,
        },
    )
    model = await detected_issue_service.get_detected_issue_scoped(
        detected_issue_id, actor.org_id
    )
    return format_response(
        detected_issue_service._to_fhir(model),
        detected_issue_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{detected_issue_id}",
    operation_id="patch_detected_issue",
    summary="Update a DetectedIssue resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_detected_issue(
    payload: DetectedIssuePatchSchema,
    request: Request,
    detected_issue_id: int = Path(
        ..., ge=1, description="Public DetectedIssue identifier."
    ),
    actor: AuthUser = Depends(require_permission("detected_issue", "update")),
    detected_issue_service: DetectedIssueService = Depends(
        get_detected_issue_service
    ),
):
    logger.info(
        "Update a DetectedIssue resource",
        extra={
            "event": "route.patch_detected_issue",
            "detected_issue_id": detected_issue_id,
        },
    )
    log_payload(logger, "detected_issue.patch.payload", payload)
    model = await detected_issue_service.patch_detected_issue(
        detected_issue_id, payload, updated_by=actor.sub, org_id=actor.org_id
    )
    return format_response(
        detected_issue_service._to_fhir(model),
        detected_issue_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_detected_issues",
    summary="List DetectedIssue resources",
    description=(
        "Search and filter DetectedIssue resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_detected_issues(
    request: Request,
    status_filter: str | None = Query(
        None,
        alias="status",
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown",
    ),
    patient: str | None = Query(
        None, description="Associated patient (e.g. 'Patient/10001')."
    ),
    author: str | None = Query(
        None, description="The provider or device that identified the issue (e.g. 'Practitioner/30001')."
    ),
    identified: date | datetime | str | None = Query(
        None, alias="identified", description="When the issue was identified."
    ),
    identifier: str | None = Query(
        None, description="Filter by business identifier system|value."
    ),
    code: str | None = Query(
        None, description="Filter by issue category code system|code or code."
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("detected_issue", "read")),
    detected_issue_service: DetectedIssueService = Depends(
        get_detected_issue_service
    ),
):
    logger.info(
        "List DetectedIssue resources",
        extra={
            "event": "route.list_detected_issues",
            "status": status_filter,
            "patient": patient,
            "author": author,
            "identified": str(identified) if identified else None,
            "identifier": identifier,
            "code": code,
            "limit": list_params.limit,
            "offset": list_params.offset,
        },
    )
    items, total = await detected_issue_service.list_detected_issues(
        org_id=actor.org_id,
        status=status_filter,
        patient=patient,
        author=author,
        identified=identified,
        identifier=identifier,
        code=code,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    return format_paginated_response(
        [detected_issue_service._to_fhir(m) for m in items],
        [detected_issue_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{detected_issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_detected_issue",
    summary="Delete a DetectedIssue resource",
    description=(
        "Deletes a DetectedIssue and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "DetectedIssue deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_detected_issue(
    detected_issue_id: int = Path(
        ..., ge=1, description="Public DetectedIssue identifier."
    ),
    actor: AuthUser = Depends(require_permission("detected_issue", "delete")),
    detected_issue_service: DetectedIssueService = Depends(
        get_detected_issue_service
    ),
):
    logger.info(
        "Delete a DetectedIssue resource",
        extra={
            "event": "route.delete_detected_issue",
            "detected_issue_id": detected_issue_id,
        },
    )
    await detected_issue_service.delete_detected_issue(
        detected_issue_id, org_id=actor.org_id
    )
    return None
