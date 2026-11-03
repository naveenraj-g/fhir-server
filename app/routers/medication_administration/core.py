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
from app.di.dependencies.medication_administration import (
    get_medication_administration_service,
)
from app.schemas.medication_administration import (
    MedicationAdministrationCreateSchema,
    MedicationAdministrationPatchSchema,
)
from app.services.medication_administration import (
    MedicationAdministrationService,
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
    operation_id="create_medication_administration",
    summary="Create a new MedicationAdministration resource",
    description=(
        "Describes the event of a patient consuming or being administered a medication. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_medication_administration(
    payload: MedicationAdministrationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_administration", "create")),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    logger.info(
        "Create a new MedicationAdministration resource",
        extra={"event": "route.create_medication_administration", "org_id": actor.org_id},
    )
    log_payload(logger, "medication_administration.create.payload", payload)
    model = await medication_administration_service.create_medication_administration(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        medication_administration_service._to_fhir(model),
        medication_administration_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_administration_id}",
    operation_id="get_medication_administration",
    summary="Get a MedicationAdministration resource by ID",
    description=(
        "Returns the complete MedicationAdministration representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication_administration(
    request: Request,
    medication_administration_id: int = Path(
        ..., ge=1, description="Public MedicationAdministration identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_administration", "read")),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    logger.info(
        "Get a MedicationAdministration resource by ID",
        extra={
            "event": "route.get_medication_administration",
            "medication_administration_id": medication_administration_id,
            "org_id": actor.org_id,
        },
    )
    model = await medication_administration_service.get_medication_administration_scoped(
        medication_administration_id, actor.org_id
    )
    return format_response(
        medication_administration_service._to_fhir(model),
        medication_administration_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{medication_administration_id}",
    operation_id="patch_medication_administration",
    summary="Update a MedicationAdministration resource (partial patch)",
    description=(
        "Updates specified fields on the MedicationAdministration resource. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_administration(
    payload: MedicationAdministrationPatchSchema,
    request: Request,
    medication_administration_id: int = Path(
        ..., ge=1, description="Public MedicationAdministration identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_administration", "update")),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    logger.info(
        "Update a MedicationAdministration resource (partial patch)",
        extra={
            "event": "route.patch_medication_administration",
            "medication_administration_id": medication_administration_id,
            "org_id": actor.org_id,
        },
    )
    log_payload(logger, "medication_administration.patch.payload", payload)
    updated = await medication_administration_service.patch_medication_administration(
        medication_administration_id, payload, actor.sub, actor.org_id
    )
    return format_response(
        medication_administration_service._to_fhir(updated),
        medication_administration_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_medication_administrations",
    summary="List MedicationAdministration resources with filtering and pagination",
    description=(
        "Search MedicationAdministration resources. Scoped to actor.org_id — an org-less token "
        "is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses=_LIST_200,
)
async def list_medication_administrations(
    request: Request,
    med_status: str | None = Query(
        None,
        alias="status",
        description="in-progress | not-done | on-hold | completed | entered-in-error | stopped | unknown.",
    ),
    subject: str | None = Query(
        None,
        description="Patient or Group receiving the medication, e.g. 'Patient/10001'.",
    ),
    patient: str | None = Query(
        None,
        description="Patient receiving the medication, e.g. 'Patient/10001'.",
    ),
    code: str | None = Query(
        None,
        description="What was administered (matches coding.code or coding.system|code).",
    ),
    category: str | None = Query(
        None,
        description="Type of medication administration.",
    ),
    effective_val: date | datetime | None = Query(
        None,
        alias="effective",
        description="Exact date/datetime of administration.",
    ),
    effective_from: date | datetime | None = Query(
        None,
        alias="effective_from",
        description="Administration interval range start.",
    ),
    effective_to: date | datetime | None = Query(
        None,
        alias="effective_to",
        description="Administration interval range end.",
    ),
    identifier: str | None = Query(
        None,
        description="External business identifier (matches value or system|value).",
    ),
    request_param: str | None = Query(
        None,
        alias="request",
        description="Request that authorized this administration, e.g. 'MedicationRequest/90001'.",
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("medication_administration", "read")),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    logger.info(
        "List MedicationAdministration resources with filtering and pagination",
        extra={"event": "route.list_medication_administrations", "org_id": actor.org_id},
    )
    models, total = await medication_administration_service.list_medication_administrations(
        org_id=actor.org_id,
        status=med_status,
        subject=subject,
        patient=patient,
        code=code,
        category=category,
        effective_val=effective_val,
        effective_from=effective_from,
        effective_to=effective_to,
        identifier=identifier,
        request=request_param,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    return format_paginated_response(
        fhir_list=[medication_administration_service._to_fhir(m) for m in models],
        plain_list=[medication_administration_service._to_plain(m) for m in models],
        total=total,
        limit=list_params.limit,
        offset=list_params.offset,
        request=request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{medication_administration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_medication_administration",
    summary="Delete a MedicationAdministration resource",
    description=(
        "Deletes a MedicationAdministration resource by ID. Scoped to the caller's own org — "
        "raises NotFoundError (404, not 403) if actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "Resource deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_medication_administration(
    medication_administration_id: int = Path(
        ..., ge=1, description="Public MedicationAdministration identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_administration", "delete")),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    logger.info(
        "Delete a MedicationAdministration resource",
        extra={
            "event": "route.delete_medication_administration",
            "medication_administration_id": medication_administration_id,
            "org_id": actor.org_id,
        },
    )
    await medication_administration_service.delete_medication_administration(
        medication_administration_id, actor.org_id
    )
