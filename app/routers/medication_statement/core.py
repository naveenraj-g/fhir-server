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
from app.di.dependencies.medication_statement import get_medication_statement_service
from app.schemas.medication_statement import (
    MedicationStatementCreateSchema,
    MedicationStatementPatchSchema,
)
from app.services.medication_statement import MedicationStatementService

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
    operation_id="create_medication_statement",
    summary="Create a new MedicationStatement resource",
    description=(
        "Record of a medication that is being consumed by a patient. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_medication_statement(
    payload: MedicationStatementCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_statement", "create")),
    medication_statement_service: MedicationStatementService = Depends(
        get_medication_statement_service
    ),
):
    logger.info(
        "Create a new MedicationStatement resource",
        extra={"event": "route.create_medication_statement", "org_id": actor.org_id},
    )
    log_payload(logger, "medication_statement.create.payload", payload)
    model = await medication_statement_service.create_medication_statement(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        medication_statement_service._to_fhir(model),
        medication_statement_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_statement_id}",
    operation_id="get_medication_statement",
    summary="Get a MedicationStatement resource by ID",
    description=(
        "Returns the complete MedicationStatement representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication_statement(
    request: Request,
    medication_statement_id: int = Path(
        ..., ge=1, description="Public MedicationStatement identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_statement", "read")),
    medication_statement_service: MedicationStatementService = Depends(
        get_medication_statement_service
    ),
):
    logger.info(
        "Get a MedicationStatement resource by ID",
        extra={
            "event": "route.get_medication_statement",
            "medication_statement_id": medication_statement_id,
        },
    )
    model = await medication_statement_service.get_medication_statement_scoped(
        medication_statement_id, actor.org_id
    )
    return format_response(
        medication_statement_service._to_fhir(model),
        medication_statement_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{medication_statement_id}",
    operation_id="patch_medication_statement",
    summary="Update a MedicationStatement resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_statement(
    payload: MedicationStatementPatchSchema,
    request: Request,
    medication_statement_id: int = Path(
        ..., ge=1, description="Public MedicationStatement identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_statement", "update")),
    medication_statement_service: MedicationStatementService = Depends(
        get_medication_statement_service
    ),
):
    logger.info(
        "Update a MedicationStatement resource",
        extra={
            "event": "route.patch_medication_statement",
            "medication_statement_id": medication_statement_id,
        },
    )
    log_payload(logger, "medication_statement.patch.payload", payload)
    updated = await medication_statement_service.patch_medication_statement(
        medication_statement_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        medication_statement_service._to_fhir(updated),
        medication_statement_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_medication_statements",
    summary="List all MedicationStatement resources",
    description=(
        "Returns a paginated list of MedicationStatement resources. Filter by status, "
        "subject/patient, code, category, effective date, identifier. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_medication_statements(
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_statement", "read")),
    statement_status: str | None = Query(
        None,
        alias="status",
        description="active | completed | entered-in-error | intended | stopped | on-hold | unknown | not-taken.",
    ),
    subject: str | None = Query(
        None, description="Who is/was taking the medication (Patient or Group reference)."
    ),
    patient: str | None = Query(
        None, description="Patient who is/was taking the medication (alias for subject)."
    ),
    code: str | None = Query(
        None, description="Code or name of medication."
    ),
    category: str | None = Query(
        None, description="Type of medication statement."
    ),
    effective_val: date | None = Query(
        None, description="Date evaluation was asserted."
    ),
    effective_from: datetime | None = Query(
        None, description="Effective date range start."
    ),
    effective_to: datetime | None = Query(
        None, description="Effective date range end."
    ),
    identifier: str | None = Query(
        None, description="Business identifier value."
    ),
    list_params: ListParams = Depends(),
    medication_statement_service: MedicationStatementService = Depends(
        get_medication_statement_service
    ),
):
    logger.info(
        "List MedicationStatement resources",
        extra={"event": "route.list_medication_statements", "org_id": actor.org_id},
    )
    items, total = await medication_statement_service.list_medication_statements(
        org_id=actor.org_id,
        status=statement_status,
        subject=subject,
        patient=patient,
        code=code,
        category=category,
        effective_val=effective_val,
        effective_from=effective_from,
        effective_to=effective_to,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [medication_statement_service._to_fhir(m) for m in items],
        [medication_statement_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{medication_statement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_medication_statement",
    summary="Delete a MedicationStatement resource",
    description=(
        "Deletes a MedicationStatement and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "MedicationStatement deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_medication_statement(
    medication_statement_id: int = Path(
        ..., ge=1, description="Public MedicationStatement identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_statement", "delete")),
    medication_statement_service: MedicationStatementService = Depends(
        get_medication_statement_service
    ),
):
    logger.info(
        "Delete a MedicationStatement resource",
        extra={
            "event": "route.delete_medication_statement",
            "medication_statement_id": medication_statement_id,
        },
    )
    await medication_statement_service.delete_medication_statement(
        medication_statement_id, org_id=actor.org_id
    )
    return None
