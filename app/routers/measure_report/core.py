from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.measure_report import get_measure_report_service
from app.schemas.measure_report import (
    MeasureReportCreateSchema,
    MeasureReportPatchSchema,
)
from app.services.measure_report import MeasureReportService

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
    operation_id="create_measure_report",
    summary="Create a new MeasureReport resource",
    description=(
        "The MeasureReport resource contains the results of the calculation of a measure. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_measure_report(
    payload: MeasureReportCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("measure_report", "create")),
    measure_report_service: MeasureReportService = Depends(get_measure_report_service),
):
    logger.info(
        "Create a new MeasureReport resource",
        extra={"event": "route.create_measure_report", "org_id": actor.org_id},
    )
    log_payload(logger, "measure_report.create.payload", payload)
    model = await measure_report_service.create_measure_report(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        measure_report_service._to_fhir(model),
        measure_report_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{measure_report_id}",
    operation_id="get_measure_report",
    summary="Get a MeasureReport resource by ID",
    description=(
        "Returns the complete MeasureReport representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_measure_report(
    request: Request,
    measure_report_id: int = Path(
        ..., ge=1, description="Public MeasureReport identifier."
    ),
    actor: AuthUser = Depends(require_permission("measure_report", "read")),
    measure_report_service: MeasureReportService = Depends(get_measure_report_service),
):
    logger.info(
        "Get a MeasureReport resource by ID",
        extra={
            "event": "route.get_measure_report",
            "measure_report_id": measure_report_id,
        },
    )
    model = await measure_report_service.get_measure_report_scoped(
        measure_report_id, actor.org_id
    )
    return format_response(
        measure_report_service._to_fhir(model),
        measure_report_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{measure_report_id}",
    operation_id="patch_measure_report",
    summary="Update a MeasureReport resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_measure_report(
    payload: MeasureReportPatchSchema,
    request: Request,
    measure_report_id: int = Path(
        ..., ge=1, description="Public MeasureReport identifier."
    ),
    actor: AuthUser = Depends(require_permission("measure_report", "update")),
    measure_report_service: MeasureReportService = Depends(get_measure_report_service),
):
    logger.info(
        "Update a MeasureReport resource",
        extra={
            "event": "route.patch_measure_report",
            "measure_report_id": measure_report_id,
        },
    )
    log_payload(logger, "measure_report.patch.payload", payload)
    model = await measure_report_service.patch_measure_report(
        measure_report_id, payload, updated_by=actor.sub, org_id=actor.org_id
    )
    return format_response(
        measure_report_service._to_fhir(model),
        measure_report_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_measure_reports",
    summary="List MeasureReport resources",
    description=(
        "Search and filter MeasureReport resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_measure_reports(
    request: Request,
    identifier: str | None = Query(
        None, description="Filter by business identifier system|value or value."
    ),
    status: str | None = Query(
        None, description="Filter by status (complete, pending, error)."
    ),
    type: str | None = Query(
        None,
        description="Filter by type (individual, subject-list, summary, data-collection).",
    ),
    measure: str | None = Query(None, description="Filter by measure canonical URL."),
    subject: str | None = Query(
        None, description="Filter by subject reference (e.g. Patient/10001)."
    ),
    reporter: str | None = Query(
        None, description="Filter by reporter reference (e.g. Practitioner/30001)."
    ),
    date: str | None = Query(
        None, description="Filter by report date (e.g. 2026-11-03)."
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("measure_report", "read")),
    measure_report_service: MeasureReportService = Depends(get_measure_report_service),
):
    logger.info(
        "List MeasureReport resources",
        extra={"event": "route.list_measure_reports", "org_id": actor.org_id},
    )
    rows, total = await measure_report_service.list_measure_reports(
        org_id=actor.org_id,
        identifier=identifier,
        status=status,
        type=type,
        measure=measure,
        subject=subject,
        reporter=reporter,
        date=date,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    fhir_list = [measure_report_service._to_fhir(r) for r in rows]
    plain_list = [measure_report_service._to_plain(r) for r in rows]
    return format_paginated_response(
        fhir_list,
        plain_list,
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{measure_report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_measure_report",
    summary="Delete a MeasureReport resource",
    description=(
        "Deletes a MeasureReport and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "MeasureReport deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_measure_report(
    measure_report_id: int = Path(
        ..., ge=1, description="Public MeasureReport identifier."
    ),
    actor: AuthUser = Depends(require_permission("measure_report", "delete")),
    measure_report_service: MeasureReportService = Depends(get_measure_report_service),
):
    logger.info(
        "Delete a MeasureReport resource",
        extra={
            "event": "route.delete_measure_report",
            "measure_report_id": measure_report_id,
        },
    )
    await measure_report_service.delete_measure_report(
        measure_report_id, org_id=actor.org_id
    )
    return None
