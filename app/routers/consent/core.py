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
from app.di.dependencies.consent import get_consent_service
from app.schemas.consent import ConsentCreateSchema, ConsentPatchSchema
from app.services.consent import ConsentService

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
    operation_id="create_consent",
    summary="Create a new Consent resource",
    description=(
        "A record of a healthcare consumer’s choices, which permits or denies "
        "identified recipient(s) or recipient role(s) to perform one or more actions "
        "within a given policy context. Accepts the full nested payload atomically in "
        "one DB transaction. `tenant_id`/`created_by` come from the verified JWT "
        "(`actor.org_id`/`actor.sub`) — an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_consent(
    payload: ConsentCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("consent", "create")),
    consent_service: ConsentService = Depends(get_consent_service),
):
    logger.info(
        "Create a new Consent resource",
        extra={"event": "route.create_consent"},
    )
    log_payload(logger, "consent.create.payload", payload)
    consent = await consent_service.create_consent(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        consent_service._to_fhir(consent),
        consent_service._to_plain(consent),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{consent_id}",
    operation_id="get_consent",
    summary="Get a Consent resource by ID",
    description=(
        "Returns the full Consent resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_consent(
    request: Request,
    consent_id: int = Path(
        ..., ge=1, description="Public consent identifier."
    ),
    actor: AuthUser = Depends(require_permission("consent", "read")),
    consent_service: ConsentService = Depends(get_consent_service),
):
    logger.info(
        "Get a Consent resource by ID",
        extra={"event": "route.get_consent", "consent_id": consent_id},
    )
    consent = await consent_service.get_consent_scoped(
        consent_id, actor.org_id
    )
    return format_response(
        consent_service._to_fhir(consent),
        consent_service._to_plain(consent),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{consent_id}",
    operation_id="patch_consent",
    summary="Update a Consent resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_consent(
    payload: ConsentPatchSchema,
    request: Request,
    consent_id: int = Path(
        ..., ge=1, description="Public consent identifier."
    ),
    actor: AuthUser = Depends(require_permission("consent", "update")),
    consent_service: ConsentService = Depends(get_consent_service),
):
    logger.info(
        "Update a Consent resource",
        extra={
            "event": "route.patch_consent",
            "consent_id": consent_id,
        },
    )
    log_payload(logger, "consent.patch.payload", payload)
    updated = await consent_service.patch_consent(
        consent_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        consent_service._to_fhir(updated),
        consent_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_consents",
    summary="List all Consent resources",
    description=(
        "Returns a paginated list of Consent resources. Filter by status, scope, "
        "category, patient, date, period, actor, action, purpose, data, identifier. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_consents(
    request: Request,
    actor: AuthUser = Depends(require_permission("consent", "read")),
    status: str | None = Query(
        None,
        description="draft | proposed | active | rejected | inactive | entered-in-error.",
    ),
    scope: str | None = Query(
        None, description="Which problem code this consent applies to."
    ),
    category: str | None = Query(
        None, description="Classification of the consent statement."
    ),
    patient: str | None = Query(
        None, description="Who the consent applies to (Patient reference)."
    ),
    date_val: date | None = Query(
        None, description="Exact date consent was created or indexed."
    ),
    date_from: datetime | None = Query(
        None, description="Consent dateTime range start."
    ),
    date_to: datetime | None = Query(
        None, description="Consent dateTime range end."
    ),
    period_from: datetime | None = Query(
        None, description="Provision period range start."
    ),
    period_to: datetime | None = Query(
        None, description="Provision period range end."
    ),
    actor_ref: str | None = Query(
        None,
        alias="actor",
        description="Who|what controlled by this rule (actor reference).",
    ),
    action: str | None = Query(
        None, description="Actions controlled by this rule."
    ),
    purpose: str | None = Query(
        None, description="Context of activities covered by this rule."
    ),
    data: str | None = Query(
        None, description="Data reference controlled by this rule."
    ),
    source_reference: str | None = Query(
        None, description="Source reference string."
    ),
    organization: str | None = Query(
        None, description="Custodian of the consent (Organization reference)."
    ),
    identifier: str | None = Query(
        None, description="Business identifier value."
    ),
    list_params: ListParams = Depends(),
    consent_service: ConsentService = Depends(get_consent_service),
):
    logger.info(
        "List Consent resources",
        extra={"event": "route.list_consents", "org_id": actor.org_id},
    )
    consents, total = await consent_service.list_consents(
        org_id=actor.org_id,
        status=status,
        scope=scope,
        category=category,
        patient=patient,
        date_val=date_val,
        date_from=date_from,
        date_to=date_to,
        period_from=period_from,
        period_to=period_to,
        actor=actor_ref,
        action=action,
        purpose=purpose,
        data=data,
        source_reference=source_reference,
        organization=organization,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [consent_service._to_fhir(c) for c in consents],
        [consent_service._to_plain(c) for c in consents],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{consent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_consent",
    summary="Delete a Consent resource",
    description=(
        "Permanently deletes the Consent and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_consent(
    consent_id: int = Path(
        ..., ge=1, description="Public consent identifier."
    ),
    actor: AuthUser = Depends(require_permission("consent", "delete")),
    consent_service: ConsentService = Depends(get_consent_service),
):
    logger.info(
        "Delete a Consent resource",
        extra={
            "event": "route.delete_consent",
            "consent_id": consent_id,
        },
    )
    await consent_service.delete_consent(consent_id, org_id=actor.org_id)
