from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.deps.diagnostic_report_deps import resolve_diagnostic_report
from app.di.dependencies.diagnostic_report import get_diagnostic_report_service
from app.models.diagnostic_report import DiagnosticReportModel
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
        "payload atomically in one DB transaction. Default (gateway-trusted) pattern: "
        "`tenant_id`/`created_by` are plain request body fields. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_diagnostic_report(
    payload: DiagnosticReportCreateSchema,
    request: Request,
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("Create a new DiagnosticReport resource", extra={"event": "route.create_diagnostic_report"})
    log_payload(logger, "diagnostic_report.create.payload", payload)
    diagnostic_report = await diagnostic_report_service.create_diagnostic_report(payload)
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
    summary="List DiagnosticReport resources owned by a given end-user",
    description=(
        "Same filters as `GET /`, scoped to the gateway-forwarded `user_id` query param "
        "(default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_diagnostic_reports(
    request: Request,
    user_id: str = Query(..., description="Gateway-forwarded ID of the end-user to scope results to."),
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID."),
    diagnostic_report_status: DiagnosticReportStatus | None = Query(
        None, alias="status", description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown."
    ),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("List DiagnosticReport resources owned by a given end-user", extra={"event": "route.list_my_diagnostic_reports"})
    items, total = await diagnostic_report_service.get_me(
        user_id=user_id, tenant_id=tenant_id, status=diagnostic_report_status,
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
        "Loaded via `resolve_diagnostic_report()` — a plain load-by-public-ID lookup with no "
        "ownership check (default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_diagnostic_report(
    request: Request,
    diagnostic_report: DiagnosticReportModel = Depends(resolve_diagnostic_report),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info(
        "Retrieve a DiagnosticReport resource by public diagnostic_report_id",
        extra={"event": "route.get_diagnostic_report_by_id", "diagnostic_report_id": diagnostic_report.diagnostic_report_id},
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
        "omitted lists are left untouched. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_diagnostic_report(
    payload: DiagnosticReportPatchSchema,
    request: Request,
    diagnostic_report_id: int = Path(..., ge=1, description="Public diagnostic_report identifier."),
    _existing: DiagnosticReportModel = Depends(resolve_diagnostic_report),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("Update a DiagnosticReport resource", extra={"event": "route.patch_diagnostic_report", "diagnostic_report_id": diagnostic_report_id})
    log_payload(logger, "diagnostic_report.patch.payload", payload)
    updated = await diagnostic_report_service.patch_diagnostic_report(diagnostic_report_id, payload)
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
        "value), plus `tenant_id`/`user_id` as explicit, gateway-forwarded query filters. "
        "Sort with `sort` (e.g. `-issued`); set `total_mode=none` to skip the COUNT(*) on "
        "large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_diagnostic_reports(
    request: Request,
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID filter."),
    user_id: str | None = Query(None, description="Gateway-forwarded end-user ID filter."),
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
        tenant_id=tenant_id, user_id=user_id, status=diagnostic_report_status,
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
    description="Permanently deletes the DiagnosticReport and all associated sub-resources. Returns 204 on success.",
    responses={**_ERR_NOT_FOUND},
)
async def delete_diagnostic_report(
    diagnostic_report_id: int = Path(..., ge=1, description="Public diagnostic_report identifier."),
    _existing: DiagnosticReportModel = Depends(resolve_diagnostic_report),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info("Delete a DiagnosticReport resource", extra={"event": "route.delete_diagnostic_report", "diagnostic_report_id": diagnostic_report_id})
    await diagnostic_report_service.delete_diagnostic_report(diagnostic_report_id)
