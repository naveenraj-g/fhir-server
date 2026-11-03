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
from app.di.dependencies.medication_dispense import (
    get_medication_dispense_service,
)
from app.models.medication_dispense import MedicationDispenseStatus
from app.schemas.medication_dispense import (
    MedicationDispenseCreateSchema,
    MedicationDispensePatchSchema,
)
from app.services.medication_dispense import (
    MedicationDispenseService,
)

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
    operation_id="create_medication_dispense",
    summary="Create a new MedicationDispense resource",
    description=(
        "Describes the event of dispensing a medication to a patient or consumer. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_medication_dispense(
    payload: MedicationDispenseCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_dispense", "create")),
    medication_dispense_service: MedicationDispenseService = Depends(
        get_medication_dispense_service
    ),
):
    logger.info(
        "Create a new MedicationDispense resource",
        extra={"event": "route.create_medication_dispense", "org_id": actor.org_id},
    )
    log_payload(logger, "medication_dispense.create.payload", payload)
    model = await medication_dispense_service.create_medication_dispense(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        medication_dispense_service._to_fhir(model),
        medication_dispense_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_dispense_id}",
    operation_id="get_medication_dispense",
    summary="Get a MedicationDispense resource by ID",
    description=(
        "Returns the complete MedicationDispense representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication_dispense(
    request: Request,
    medication_dispense_id: int = Path(
        ..., ge=1, description="Public MedicationDispense identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_dispense", "read")),
    medication_dispense_service: MedicationDispenseService = Depends(
        get_medication_dispense_service
    ),
):
    logger.info(
        "Get a MedicationDispense resource by ID",
        extra={
            "event": "route.get_medication_dispense",
            "medication_dispense_id": medication_dispense_id,
            "org_id": actor.org_id,
        },
    )
    model = await medication_dispense_service.get_medication_dispense_scoped(
        medication_dispense_id, actor.org_id
    )
    return format_response(
        medication_dispense_service._to_fhir(model),
        medication_dispense_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{medication_dispense_id}",
    operation_id="patch_medication_dispense",
    summary="Update a MedicationDispense resource (partial patch)",
    description=(
        "Updates specified fields on the MedicationDispense resource. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_dispense(
    payload: MedicationDispensePatchSchema,
    request: Request,
    medication_dispense_id: int = Path(
        ..., ge=1, description="Public MedicationDispense identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_dispense", "update")),
    medication_dispense_service: MedicationDispenseService = Depends(
        get_medication_dispense_service
    ),
):
    logger.info(
        "Update a MedicationDispense resource (partial patch)",
        extra={
            "event": "route.patch_medication_dispense",
            "medication_dispense_id": medication_dispense_id,
            "org_id": actor.org_id,
        },
    )
    log_payload(logger, "medication_dispense.patch.payload", payload)
    model = await medication_dispense_service.patch_medication_dispense(
        medication_dispense_id, payload, actor.sub, actor.org_id
    )
    return format_response(
        medication_dispense_service._to_fhir(model),
        medication_dispense_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_medication_dispenses",
    summary="List MedicationDispense resources",
    description=(
        "Returns a paginated list of MedicationDispense resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses=_LIST_200,
)
async def list_medication_dispenses(
    request: Request,
    dispense_status: MedicationDispenseStatus | None = Query(
        None,
        alias="status",
        description="Filter by status (preparation | in-progress | cancelled | on-hold | completed | entered-in-error | stopped | declined | unknown).",
    ),
    subject: str | None = Query(
        None,
        description="Filter by subject reference, e.g. 'Patient/10001'.",
    ),
    patient: str | None = Query(
        None,
        description="Alias for subject filter, e.g. 'Patient/10001'.",
    ),
    code: str | None = Query(
        None,
        description="Filter by medication code (matches system|code or code).",
    ),
    category: str | None = Query(
        None,
        description="Type of medication dispense.",
    ),
    dispense_type: str | None = Query(
        None,
        alias="type",
        description="Trial fill, partial fill, emergency fill, etc.",
    ),
    when_prepared_val: date | datetime | None = Query(
        None,
        alias="whenprepared",
        description="Exact date/datetime product was packaged and reviewed.",
    ),
    when_prepared_from: date | datetime | None = Query(
        None,
        alias="whenprepared_from",
        description="Packaging interval range start.",
    ),
    when_prepared_to: date | datetime | None = Query(
        None,
        alias="whenprepared_to",
        description="Packaging interval range end.",
    ),
    when_handed_over_val: date | datetime | None = Query(
        None,
        alias="whenhandedover",
        description="Exact date/datetime product was handed over.",
    ),
    when_handed_over_from: date | datetime | None = Query(
        None,
        alias="whenhandedover_from",
        description="Handover interval range start.",
    ),
    when_handed_over_to: date | datetime | None = Query(
        None,
        alias="whenhandedover_to",
        description="Handover interval range end.",
    ),
    identifier: str | None = Query(
        None,
        description="External business identifier (matches value or system|value).",
    ),
    destination: str | None = Query(
        None,
        description="Where medication was sent, e.g. 'Location/230001'.",
    ),
    receiver: str | None = Query(
        None,
        description="Who collected medication, e.g. 'Patient/10001'.",
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("medication_dispense", "read")),
    medication_dispense_service: MedicationDispenseService = Depends(
        get_medication_dispense_service
    ),
):
    logger.info(
        "List MedicationDispense resources with filtering and pagination",
        extra={"event": "route.list_medication_dispenses", "org_id": actor.org_id},
    )
    models, total = await medication_dispense_service.list_medication_dispenses(
        org_id=actor.org_id,
        status=dispense_status,
        subject=subject,
        patient=patient,
        code=code,
        category=category,
        type=dispense_type,
        when_prepared_val=when_prepared_val,
        when_prepared_from=when_prepared_from,
        when_prepared_to=when_prepared_to,
        when_handed_over_val=when_handed_over_val,
        when_handed_over_from=when_handed_over_from,
        when_handed_over_to=when_handed_over_to,
        identifier=identifier,
        destination=destination,
        receiver=receiver,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    return format_paginated_response(
        fhir_list=[medication_dispense_service._to_fhir(m) for m in models],
        plain_list=[medication_dispense_service._to_plain(m) for m in models],
        total=total,
        limit=list_params.limit,
        offset=list_params.offset,
        request=request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{medication_dispense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_medication_dispense",
    summary="Delete a MedicationDispense resource",
    description=(
        "Deletes a MedicationDispense resource by ID. Scoped to the caller's own org — "
        "raises NotFoundError (404, not 403) if actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "Resource deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_medication_dispense(
    medication_dispense_id: int = Path(
        ..., ge=1, description="Public MedicationDispense identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_dispense", "delete")),
    medication_dispense_service: MedicationDispenseService = Depends(
        get_medication_dispense_service
    ),
):
    logger.info(
        "Delete a MedicationDispense resource",
        extra={
            "event": "route.delete_medication_dispense",
            "medication_dispense_id": medication_dispense_id,
            "org_id": actor.org_id,
        },
    )
    await medication_dispense_service.delete_medication_dispense(
        medication_dispense_id, actor.org_id
    )
