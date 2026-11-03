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
from app.di.dependencies.medication import get_medication_service
from app.models.medication import MedicationStatus
from app.schemas.medication import (
    MedicationCreateSchema,
    MedicationPatchSchema,
)
from app.services.medication import MedicationService

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
    operation_id="create_medication",
    summary="Create a new Medication resource",
    description=(
        "This resource is primarily used for the identification and definition of a medication "
        "for the purposes of prescribing, dispensing, and administering a medication as well as "
        "for making statements about medication use. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_medication(
    payload: MedicationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("medication", "create")),
    medication_service: MedicationService = Depends(get_medication_service),
):
    logger.info(
        "Create a new Medication resource",
        extra={"event": "route.create_medication", "org_id": actor.org_id},
    )
    log_payload(logger, "medication.create.payload", payload)
    model = await medication_service.create_medication(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        medication_service._to_fhir(model),
        medication_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_id}",
    operation_id="get_medication",
    summary="Get a Medication resource by ID",
    description=(
        "Returns the complete Medication representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication(
    request: Request,
    medication_id: int = Path(
        ..., ge=1, description="Public Medication identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication", "read")),
    medication_service: MedicationService = Depends(get_medication_service),
):
    logger.info(
        "Get a Medication resource by ID",
        extra={
            "event": "route.get_medication",
            "medication_id": medication_id,
            "org_id": actor.org_id,
        },
    )
    model = await medication_service.get_medication_scoped(
        medication_id, actor.org_id
    )
    return format_response(
        medication_service._to_fhir(model),
        medication_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{medication_id}",
    operation_id="patch_medication",
    summary="Update a Medication resource (partial patch)",
    description=(
        "Updates specified fields on the Medication resource. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication(
    payload: MedicationPatchSchema,
    request: Request,
    medication_id: int = Path(
        ..., ge=1, description="Public Medication identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication", "update")),
    medication_service: MedicationService = Depends(get_medication_service),
):
    logger.info(
        "Update a Medication resource (partial patch)",
        extra={
            "event": "route.patch_medication",
            "medication_id": medication_id,
            "org_id": actor.org_id,
        },
    )
    log_payload(logger, "medication.patch.payload", payload)
    model = await medication_service.patch_medication(
        medication_id, payload, actor.sub, actor.org_id
    )
    return format_response(
        medication_service._to_fhir(model),
        medication_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_medications",
    summary="List Medication resources",
    description=(
        "Returns a paginated list of Medication resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses=_LIST_200,
)
async def list_medications(
    request: Request,
    med_status: MedicationStatus | None = Query(
        None,
        alias="status",
        description="Filter by status (active | inactive | entered-in-error).",
    ),
    code: str | None = Query(
        None,
        description="Filter by medication code (matches system|code or code).",
    ),
    manufacturer: str | None = Query(
        None,
        description="Filter by manufacturer reference, e.g. 'Organization/190001'.",
    ),
    form: str | None = Query(
        None,
        description="Filter by medication form (matches system|code or code).",
    ),
    ingredient: str | None = Query(
        None,
        description="Filter by ingredient item reference, e.g. 'Substance/101' or 'Medication/250001'.",
    ),
    ingredient_code: str | None = Query(
        None,
        alias="ingredient-code",
        description="Filter by ingredient item code (matches system|code or code).",
    ),
    lot_number: str | None = Query(
        None,
        alias="lot-number",
        description="Filter by batch lot number.",
    ),
    expiration_date: date | datetime | None = Query(
        None,
        alias="expiration-date",
        description="Filter by batch expiration date.",
    ),
    identifier: str | None = Query(
        None,
        description="External business identifier (matches value or system|value).",
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("medication", "read")),
    medication_service: MedicationService = Depends(get_medication_service),
):
    logger.info(
        "List Medication resources with filtering and pagination",
        extra={"event": "route.list_medications", "org_id": actor.org_id},
    )
    models, total = await medication_service.list_medications(
        org_id=actor.org_id,
        code=code,
        status=med_status,
        manufacturer=manufacturer,
        form=form,
        ingredient=ingredient,
        ingredient_code=ingredient_code,
        lot_number=lot_number,
        expiration_date=expiration_date,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    return format_paginated_response(
        fhir_list=[medication_service._to_fhir(m) for m in models],
        plain_list=[medication_service._to_plain(m) for m in models],
        total=total,
        limit=list_params.limit,
        offset=list_params.offset,
        request=request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{medication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_medication",
    summary="Delete a Medication resource",
    description=(
        "Deletes a Medication resource by ID. Scoped to the caller's own org — "
        "raises NotFoundError (404, not 403) if actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "Resource deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_medication(
    medication_id: int = Path(
        ..., ge=1, description="Public Medication identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication", "delete")),
    medication_service: MedicationService = Depends(get_medication_service),
):
    logger.info(
        "Delete a Medication resource",
        extra={
            "event": "route.delete_medication",
            "medication_id": medication_id,
            "org_id": actor.org_id,
        },
    )
    await medication_service.delete_medication(medication_id, actor.org_id)
