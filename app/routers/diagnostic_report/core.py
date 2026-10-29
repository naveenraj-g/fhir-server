from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.diagnostic_report import get_diagnostic_report_service
from app.schemas.diagnostic_report import DiagnosticReportCreateSchema, DiagnosticReportPatchSchema
from app.schemas.enums import DiagnosticReportStatus
from app.services.diagnostic_report import DiagnosticReportService

from ._responses import _CONTENT_NEG, _ERR_NOT_FOUND, _ERR_VALIDATION, _LIST_200, _SINGLE_200, _SINGLE_201

router = APIRouter()

logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_diagnostic_report",
    summary="Create a new DiagnosticReport resource",
    description=(
        "The findings and interpretation of diagnostic tests performed on patients, groups, "
        "devices, locations, and/or specimens derived from these. Accepts the full nested "
        "payload atomically in one DB transaction. `tenant_id`/`created_by` come from the "
        "verified JWT (`actor.org_id`/`actor.sub`) — an org-less token is rejected outright "
        "(403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_diagnostic_report(
    payload: DiagnosticReportCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("diagnostic_report", "create")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("Create a new DiagnosticReport resource", extra={"event": "route.create_diagnostic_report"})
    log_payload(logger, "diagnostic_report.create.payload", payload)
    diagnostic_report = await diagnostic_report_service.create_diagnostic_report(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        diagnostic_report_service._to_fhir(diagnostic_report),
        diagnostic_report_service._to_plain(diagnostic_report),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Me (must come before /{diagnostic_report_id}) ────────────────────────────────


@router.get(
    "/me",
    operation_id="list_my_diagnostic_reports",
    summary="List DiagnosticReport resources owned by the authenticated end-user",
    description=(
        "Same filters as `GET /`, always additionally scoped to the authenticated "
        "end-user's own `user_id`, on top of the caller's own org (from the verified "
        "token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_diagnostic_reports(
    request: Request,
    actor: AuthUser = Depends(require_permission("diagnostic_report", "read")),
    diagnostic_report_status: DiagnosticReportStatus | None = Query(
        None, alias="status", description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown."
    ),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("List DiagnosticReport resources owned by the authenticated end-user", extra={"event": "route.list_my_diagnostic_reports"})
    items, total = await diagnostic_report_service.get_me(
        user_id=actor.sub, org_id=actor.org_id, status=diagnostic_report_status,
        subject=subject, identifier=identifier, limit=params.limit, offset=params.offset,
        sort=params.sort, total_mode=params.total_mode,
    )
    return format_paginated_response(
        [diagnostic_report_service._to_fhir(d) for d in items],
        [diagnostic_report_service._to_plain(d) for d in items],
        total, params.limit, params.offset, request,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{diagnostic_report_id}",
    operation_id="get_diagnostic_report_by_id",
    summary="Retrieve a DiagnosticReport resource by public diagnostic_report_id",
    description=(
        "Scoped to the caller's own org — get_diagnostic_report_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_diagnostic_report(
    request: Request,
    diagnostic_report_id: int = Path(..., ge=1, description="Public diagnostic_report identifier."),
    actor: AuthUser = Depends(require_permission("diagnostic_report", "read")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info(
        "Retrieve a DiagnosticReport resource by public diagnostic_report_id",
        extra={"event": "route.get_diagnostic_report_by_id", "diagnostic_report_id": diagnostic_report_id},
    )
    diagnostic_report = await diagnostic_report_service.get_diagnostic_report_scoped(
        diagnostic_report_id, actor.org_id
    )
    return format_response(
        diagnostic_report_service._to_fhir(diagnostic_report),
        diagnostic_report_service._to_plain(diagnostic_report),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{diagnostic_report_id}",
    operation_id="patch_diagnostic_report",
    summary="Update a DiagnosticReport resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (even `[]`) atomically replaces the corresponding rows; "
        "omitted lists are left untouched. Scoped to the caller's own org — "
        "patch_diagnostic_report() raises NotFoundError (404, not 403) if actor.org_id "
        "doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_diagnostic_report(
    payload: DiagnosticReportPatchSchema,
    request: Request,
    diagnostic_report_id: int = Path(..., ge=1, description="Public diagnostic_report identifier."),
    actor: AuthUser = Depends(require_permission("diagnostic_report", "update")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("Update a DiagnosticReport resource", extra={"event": "route.patch_diagnostic_report", "diagnostic_report_id": diagnostic_report_id})
    log_payload(logger, "diagnostic_report.patch.payload", payload)
    updated = await diagnostic_report_service.patch_diagnostic_report(
        diagnostic_report_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        diagnostic_report_service._to_fhir(updated),
        diagnostic_report_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_diagnostic_reports",
    summary="List all DiagnosticReport resources",
    description=(
        "Returns a paginated list of DiagnosticReport resources, matching a subset of the "
        "search parameters documented at https://www.hl7.org/fhir/R4/diagnosticreport.html#search. "
        "Filter by `status`, `subject` (exact), `identifier` (exact business-identifier "
        "value). Always scoped to the caller's own org (from the verified token) — "
        "`org_id` is not a client-suppliable filter. Sort with `sort` (e.g. `-issued`); "
        "set `total_mode=none` to skip the COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_diagnostic_reports(
    request: Request,
    actor: AuthUser = Depends(require_permission("diagnostic_report", "read")),
    diagnostic_report_status: DiagnosticReportStatus | None = Query(
        None, alias="status", description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown."
    ),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("List all DiagnosticReport resources", extra={"event": "route.list_diagnostic_reports"})
    items, total = await diagnostic_report_service.list_diagnostic_reports(
        org_id=actor.org_id, status=diagnostic_report_status,
        subject=subject, identifier=identifier, limit=params.limit, offset=params.offset,
        sort=params.sort, total_mode=params.total_mode,
    )
    return format_paginated_response(
        [diagnostic_report_service._to_fhir(d) for d in items],
        [diagnostic_report_service._to_plain(d) for d in items],
        total, params.limit, params.offset, request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{diagnostic_report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_diagnostic_report",
    summary="Delete a DiagnosticReport resource",
    description=(
        "Permanently deletes the DiagnosticReport and all associated sub-resources. Scoped "
        "to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_diagnostic_report(
    diagnostic_report_id: int = Path(..., ge=1, description="Public diagnostic_report identifier."),
    actor: AuthUser = Depends(require_permission("diagnostic_report", "delete")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("Delete a DiagnosticReport resource", extra={"event": "route.delete_diagnostic_report", "diagnostic_report_id": diagnostic_report_id})
    await diagnostic_report_service.delete_diagnostic_report(diagnostic_report_id, org_id=actor.org_id)
