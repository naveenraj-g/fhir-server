from datetime import date, datetime

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.procedure import get_procedure_service
from app.schemas.procedure import ProcedureCreateSchema, ProcedurePatchSchema
from app.services.procedure import ProcedureService

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
    operation_id="create_procedure",
    summary="Create a new Procedure resource",
    description=(
        "An action that is or was performed on or for a patient or subject. "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_procedure(
    payload: ProcedureCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("procedure", "create")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    logger.info(
        "Create a new Procedure resource",
        extra={"event": "route.create_procedure"},
    )
    log_payload(logger, "procedure.create.payload", payload)
    proc = await procedure_service.create_procedure(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        procedure_service._to_fhir(proc),
        procedure_service._to_plain(proc),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{procedure_id}",
    operation_id="get_procedure",
    summary="Get a Procedure resource by ID",
    description=(
        "Returns the full Procedure resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_procedure(
    request: Request,
    procedure_id: int = Path(
        ..., ge=1, description="Public procedure identifier."
    ),
    actor: AuthUser = Depends(require_permission("procedure", "read")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    logger.info(
        "Get a Procedure resource by ID",
        extra={"event": "route.get_procedure", "procedure_id": procedure_id},
    )
    proc = await procedure_service.get_procedure_scoped(
        procedure_id, actor.org_id
    )
    return format_response(
        procedure_service._to_fhir(proc),
        procedure_service._to_plain(proc),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{procedure_id}",
    operation_id="patch_procedure",
    summary="Update a Procedure resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_procedure(
    payload: ProcedurePatchSchema,
    request: Request,
    procedure_id: int = Path(
        ..., ge=1, description="Public procedure identifier."
    ),
    actor: AuthUser = Depends(require_permission("procedure", "update")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    logger.info(
        "Update a Procedure resource",
        extra={
            "event": "route.patch_procedure",
            "procedure_id": procedure_id,
        },
    )
    log_payload(logger, "procedure.patch.payload", payload)
    updated = await procedure_service.patch_procedure(
        procedure_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        procedure_service._to_fhir(updated),
        procedure_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_procedures",
    summary="List all Procedure resources",
    description=(
        "Returns a paginated list of Procedure resources. Filter by status, "
        "patient/subject, encounter, code, date, location, based_on, part_of, category, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_procedures(
    request: Request,
    actor: AuthUser = Depends(require_permission("procedure", "read")),
    status: str | None = Query(
        None, description="Status code (e.g. preparation, in-progress, completed, etc.)."
    ),
    patient: str | None = Query(None, description="Patient reference (e.g. Patient/10001)."),
    subject: str | None = Query(None, description="Subject reference (e.g. Patient/10001)."),
    encounter: str | None = Query(None, description="Encounter reference (e.g. Encounter/20001)."),
    code: str | None = Query(None, description="Procedure code (matches text or coding.code)."),
    date_val: date | None = Query(None, alias="date", description="Exact performed date (YYYY-MM-DD)."),
    date_from: date | datetime | None = Query(None, description="Performed date on or after."),
    date_to: date | datetime | None = Query(None, description="Performed date on or before."),
    location: str | None = Query(None, description="Location reference (e.g. Location/230001)."),
    based_on: str | None = Query(None, description="basedOn reference (e.g. CarePlan/290001)."),
    part_of: str | None = Query(None, description="partOf reference."),
    category: str | None = Query(None, description="Category code."),
    identifier: str | None = Query(None, description="Business identifier value."),
    list_params: ListParams = Depends(),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    logger.info(
        "List Procedure resources",
        extra={"event": "route.list_procedures", "org_id": actor.org_id},
    )
    procedures, total = await procedure_service.list_procedures(
        org_id=actor.org_id,
        status=status,
        patient=patient,
        subject=subject,
        encounter=encounter,
        code=code,
        date_val=date_val,
        date_from=date_from,
        date_to=date_to,
        location=location,
        based_on=based_on,
        part_of=part_of,
        category=category,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [procedure_service._to_fhir(p) for p in procedures],
        [procedure_service._to_plain(p) for p in procedures],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{procedure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_procedure",
    summary="Delete a Procedure resource",
    description=(
        "Permanently deletes the Procedure and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_procedure(
    procedure_id: int = Path(
        ..., ge=1, description="Public procedure identifier."
    ),
    actor: AuthUser = Depends(require_permission("procedure", "delete")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    logger.info(
        "Delete a Procedure resource",
        extra={
            "event": "route.delete_procedure",
            "procedure_id": procedure_id,
        },
    )
    await procedure_service.delete_procedure(
        procedure_id, org_id=actor.org_id
    )
