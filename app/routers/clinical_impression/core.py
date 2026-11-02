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
from app.di.dependencies.clinical_impression import get_clinical_impression_service
from app.schemas.clinical_impression import (
    ClinicalImpressionCreateSchema,
    ClinicalImpressionPatchSchema,
)
from app.services.clinical_impression import ClinicalImpressionService

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
    operation_id="create_clinical_impression",
    summary="Create a new ClinicalImpression resource",
    description=(
        "A record of a clinical assessment performed to determine what problem(s) may "
        "affect the patient and before planning the treatments or management strategies. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_clinical_impression(
    payload: ClinicalImpressionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("clinical_impression", "create")),
    clinical_impression_service: ClinicalImpressionService = Depends(
        get_clinical_impression_service
    ),
):
    logger.info(
        "Create a new ClinicalImpression resource",
        extra={"event": "route.create_clinical_impression", "org_id": actor.org_id},
    )
    log_payload(logger, "clinical_impression.create.payload", payload)
    model = await clinical_impression_service.create_clinical_impression(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        clinical_impression_service._to_fhir(model),
        clinical_impression_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{clinical_impression_id}",
    operation_id="get_clinical_impression",
    summary="Get a ClinicalImpression resource by ID",
    description=(
        "Returns the complete ClinicalImpression representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_clinical_impression(
    request: Request,
    clinical_impression_id: int = Path(
        ..., ge=1, description="Public ClinicalImpression identifier."
    ),
    actor: AuthUser = Depends(require_permission("clinical_impression", "read")),
    clinical_impression_service: ClinicalImpressionService = Depends(
        get_clinical_impression_service
    ),
):
    logger.info(
        "Get a ClinicalImpression resource by ID",
        extra={
            "event": "route.get_clinical_impression",
            "clinical_impression_id": clinical_impression_id,
        },
    )
    model = await clinical_impression_service.get_clinical_impression_scoped(
        clinical_impression_id, actor.org_id
    )
    return format_response(
        clinical_impression_service._to_fhir(model),
        clinical_impression_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{clinical_impression_id}",
    operation_id="patch_clinical_impression",
    summary="Update a ClinicalImpression resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_clinical_impression(
    payload: ClinicalImpressionPatchSchema,
    request: Request,
    clinical_impression_id: int = Path(
        ..., ge=1, description="Public ClinicalImpression identifier."
    ),
    actor: AuthUser = Depends(require_permission("clinical_impression", "update")),
    clinical_impression_service: ClinicalImpressionService = Depends(
        get_clinical_impression_service
    ),
):
    logger.info(
        "Update a ClinicalImpression resource",
        extra={
            "event": "route.patch_clinical_impression",
            "clinical_impression_id": clinical_impression_id,
        },
    )
    log_payload(logger, "clinical_impression.patch.payload", payload)
    model = await clinical_impression_service.patch_clinical_impression(
        clinical_impression_id, payload, updated_by=actor.sub, org_id=actor.org_id
    )
    return format_response(
        clinical_impression_service._to_fhir(model),
        clinical_impression_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_clinical_impressions",
    summary="List ClinicalImpression resources",
    description=(
        "Search and filter ClinicalImpression resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_clinical_impressions(
    request: Request,
    clinical_impression_status: str | None = Query(
        None,
        alias="status",
        description="in-progress | completed | entered-in-error",
    ),
    subject: str | None = Query(
        None, description="Patient or group impression is about (e.g. 'Patient/10001')."
    ),
    encounter: str | None = Query(
        None, description="Encounter created as part of (e.g. 'Encounter/20001')."
    ),
    assessor: str | None = Query(
        None, description="The clinician performing assessment (e.g. 'Practitioner/30001')."
    ),
    date_val: date | datetime | str | None = Query(
        None, alias="date", description="When the assessment was documented."
    ),
    identifier: str | None = Query(
        None, description="Filter by business identifier system|value."
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("clinical_impression", "read")),
    clinical_impression_service: ClinicalImpressionService = Depends(
        get_clinical_impression_service
    ),
):
    logger.info(
        "List ClinicalImpression resources",
        extra={
            "event": "route.list_clinical_impressions",
            "status": clinical_impression_status,
            "subject": subject,
            "encounter": encounter,
            "assessor": assessor,
            "date": str(date_val) if date_val else None,
            "identifier": identifier,
            "limit": list_params.limit,
            "offset": list_params.offset,
        },
    )
    items, total = await clinical_impression_service.list_clinical_impressions(
        org_id=actor.org_id,
        status=clinical_impression_status,
        subject=subject,
        encounter=encounter,
        assessor=assessor,
        date_val=date_val,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    return format_paginated_response(
        [clinical_impression_service._to_fhir(m) for m in items],
        [clinical_impression_service._to_plain(m) for m in items],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{clinical_impression_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_clinical_impression",
    summary="Delete a ClinicalImpression resource",
    description=(
        "Deletes a ClinicalImpression and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "ClinicalImpression deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_clinical_impression(
    clinical_impression_id: int = Path(
        ..., ge=1, description="Public ClinicalImpression identifier."
    ),
    actor: AuthUser = Depends(require_permission("clinical_impression", "delete")),
    clinical_impression_service: ClinicalImpressionService = Depends(
        get_clinical_impression_service
    ),
):
    logger.info(
        "Delete a ClinicalImpression resource",
        extra={
            "event": "route.delete_clinical_impression",
            "clinical_impression_id": clinical_impression_id,
        },
    )
    await clinical_impression_service.delete_clinical_impression(
        clinical_impression_id, org_id=actor.org_id
    )
    return None
