from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.medication_knowledge import get_medication_knowledge_service
from app.models.medication_knowledge import MedicationKnowledgeStatus
from app.schemas.medication_knowledge import (
    MedicationKnowledgeCreateSchema,
    MedicationKnowledgePatchSchema,
)
from app.services.medication_knowledge import MedicationKnowledgeService

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
    operation_id="create_medication_knowledge",
    summary="Create a new MedicationKnowledge resource",
    description=(
        "Information about a medication that is used to support knowledge."
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_medication_knowledge(
    payload: MedicationKnowledgeCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_knowledge", "create")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    logger.info(
        "Create a new MedicationKnowledge resource",
        extra={"event": "route.create_medication_knowledge", "org_id": actor.org_id},
    )
    log_payload(logger, "medication_knowledge.create.payload", payload)
    model = await medication_knowledge_service.create_medication_knowledge(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        medication_knowledge_service._to_fhir(model),
        medication_knowledge_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_knowledge_id}",
    operation_id="get_medication_knowledge",
    summary="Get a MedicationKnowledge resource by ID",
    description=(
        "Returns the complete MedicationKnowledge representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication_knowledge(
    request: Request,
    medication_knowledge_id: int = Path(
        ..., ge=1, description="Public MedicationKnowledge identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_knowledge", "read")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    logger.info(
        "Get a MedicationKnowledge resource by ID",
        extra={
            "event": "route.get_medication_knowledge",
            "medication_knowledge_id": medication_knowledge_id,
            "org_id": actor.org_id,
        },
    )
    model = await medication_knowledge_service.get_medication_knowledge_scoped(
        medication_knowledge_id, actor.org_id
    )
    return format_response(
        medication_knowledge_service._to_fhir(model),
        medication_knowledge_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{medication_knowledge_id}",
    operation_id="patch_medication_knowledge",
    summary="Update a MedicationKnowledge resource partially",
    description=(
        "Applies a partial update. Only fields explicitly set in the request body are modified; "
        "null clears a field. Validates against base FHIR R4 before writing. "
        "Scoped to the caller's own org — raises 404 (not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_knowledge(
    payload: MedicationKnowledgePatchSchema,
    request: Request,
    medication_knowledge_id: int = Path(
        ..., ge=1, description="Public MedicationKnowledge identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_knowledge", "update")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    logger.info(
        "Update a MedicationKnowledge resource partially",
        extra={
            "event": "route.patch_medication_knowledge",
            "medication_knowledge_id": medication_knowledge_id,
            "org_id": actor.org_id,
        },
    )
    log_payload(logger, "medication_knowledge.patch.payload", payload)
    model = await medication_knowledge_service.patch_medication_knowledge(
        medication_knowledge_id,
        payload,
        updated_by=actor.sub,
        org_id=actor.org_id,
    )
    return format_response(
        medication_knowledge_service._to_fhir(model),
        medication_knowledge_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_medication_knowledge",
    summary="List MedicationKnowledge resources",
    description=(
        "Returns a paginated list of MedicationKnowledge resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses=_LIST_200,
)
async def list_medication_knowledge(
    request: Request,
    mk_status: MedicationKnowledgeStatus | None = Query(
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
    dose_form: str | None = Query(
        None,
        description="Filter by dose form (matches system|code or code).",
    ),
    monitoring_program: str | None = Query(
        None,
        description="Filter by monitoring program name or type.",
    ),
    ingredient: str | None = Query(
        None,
        description="Filter by ingredient reference (Substance/Medication).",
    ),
    ingredient_code: str | None = Query(
        None,
        description="Filter by ingredient code or display.",
    ),
    pagination: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("medication_knowledge", "read")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    logger.info(
        "List MedicationKnowledge resources",
        extra={"event": "route.list_medication_knowledge", "org_id": actor.org_id},
    )
    models, total = await medication_knowledge_service.list_medication_knowledge(
        org_id=actor.org_id,
        code=code,
        status=mk_status,
        manufacturer=manufacturer,
        dose_form=dose_form,
        monitoring_program=monitoring_program,
        ingredient=ingredient,
        ingredient_code=ingredient_code,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=pagination.sort,
    )
    fhir_list = [medication_knowledge_service._to_fhir(m) for m in models]
    plain_list = [medication_knowledge_service._to_plain(m) for m in models]
    return format_paginated_response(
        fhir_list,
        plain_list,
        total,
        pagination.limit,
        pagination.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{medication_knowledge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_medication_knowledge",
    summary="Delete a MedicationKnowledge resource",
    description=(
        "Permanently deletes a MedicationKnowledge resource and its child rows. "
        "Scoped to the caller's own org — raises 404 (not 403) if actor.org_id doesn't match."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_medication_knowledge(
    medication_knowledge_id: int = Path(
        ..., ge=1, description="Public MedicationKnowledge identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_knowledge", "delete")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    logger.info(
        "Delete a MedicationKnowledge resource",
        extra={
            "event": "route.delete_medication_knowledge",
            "medication_knowledge_id": medication_knowledge_id,
            "org_id": actor.org_id,
        },
    )
    await medication_knowledge_service.delete_medication_knowledge(
        medication_knowledge_id, org_id=actor.org_id
    )
