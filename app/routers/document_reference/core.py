from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.document_reference import get_document_reference_service
from app.schemas.document_reference import (
    DocumentReferenceCreateSchema,
    DocumentReferencePatchSchema,
)
from app.services.document_reference import DocumentReferenceService

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
    operation_id="create_document_reference",
    summary="Create a new DocumentReference resource",
    description=(
        "A reference to a document of any kind for any purpose. "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_document_reference(
    payload: DocumentReferenceCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("document_reference", "create")),
    document_reference_service: DocumentReferenceService = Depends(
        get_document_reference_service
    ),
):
    logger.info(
        "Create a new DocumentReference resource",
        extra={"event": "route.create_document_reference"},
    )
    log_payload(logger, "document_reference.create.payload", payload)
    doc_ref = await document_reference_service.create_document_reference(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        document_reference_service._to_fhir(doc_ref),
        document_reference_service._to_plain(doc_ref),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{document_reference_id}",
    operation_id="get_document_reference_by_id",
    summary="Retrieve a DocumentReference resource by public document_reference_id",
    description=(
        "Scoped to the caller's own org — get_document_reference_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_document_reference(
    request: Request,
    document_reference_id: int = Path(
        ..., ge=1, description="Public document_reference identifier."
    ),
    actor: AuthUser = Depends(require_permission("document_reference", "read")),
    document_reference_service: DocumentReferenceService = Depends(
        get_document_reference_service
    ),
):
    logger.info(
        "Retrieve a DocumentReference resource by public document_reference_id",
        extra={
            "event": "route.get_document_reference_by_id",
            "document_reference_id": document_reference_id,
        },
    )
    doc_ref = await document_reference_service.get_document_reference_scoped(
        document_reference_id, actor.org_id
    )
    return format_response(
        document_reference_service._to_fhir(doc_ref),
        document_reference_service._to_plain(doc_ref),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{document_reference_id}",
    operation_id="patch_document_reference",
    summary="Update a DocumentReference resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_document_reference(
    payload: DocumentReferencePatchSchema,
    request: Request,
    document_reference_id: int = Path(
        ..., ge=1, description="Public document_reference identifier."
    ),
    actor: AuthUser = Depends(require_permission("document_reference", "update")),
    document_reference_service: DocumentReferenceService = Depends(
        get_document_reference_service
    ),
):
    logger.info(
        "Update a DocumentReference resource",
        extra={
            "event": "route.patch_document_reference",
            "document_reference_id": document_reference_id,
        },
    )
    log_payload(logger, "document_reference.patch.payload", payload)
    updated = await document_reference_service.patch_document_reference(
        document_reference_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        document_reference_service._to_fhir(updated),
        document_reference_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_document_references",
    summary="List all DocumentReference resources",
    description=(
        "Returns a paginated list of DocumentReference resources. Filter by status, "
        "doc_status, type, category, subject, author, custodian, authenticator, "
        "relates_to, identifier, description. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_document_references(
    request: Request,
    actor: AuthUser = Depends(require_permission("document_reference", "read")),
    status: str | None = Query(
        None, description="Status code (e.g. current, superseded, entered-in-error)."
    ),
    doc_status: str | None = Query(
        None, description="Document status code (e.g. preliminary, final, amended)."
    ),
    type: str | None = Query(None, description="Document type code."),
    category: str | None = Query(None, description="Document category code."),
    subject: str | None = Query(
        None, description="Subject reference string, e.g. Patient/10001."
    ),
    author: str | None = Query(
        None, description="Author reference string, e.g. Practitioner/30001."
    ),
    custodian: str | None = Query(
        None, description="Custodian reference string, e.g. Organization/190001."
    ),
    authenticator: str | None = Query(
        None, description="Authenticator reference string, e.g. Practitioner/30001."
    ),
    relates_to: str | None = Query(
        None, description="Relates-to target reference string, e.g. DocumentReference/320002."
    ),
    identifier: str | None = Query(
        None, description="Exact match on identifier value."
    ),
    description: str | None = Query(
        None, description="Partial/exact match on description."
    ),
    params: ListParams = Depends(),
    document_reference_service: DocumentReferenceService = Depends(
        get_document_reference_service
    ),
):
    logger.info(
        "List all DocumentReference resources",
        extra={"event": "route.list_document_references"},
    )
    items, total = await document_reference_service.list_document_references(
        org_id=actor.org_id,
        status=status,
        doc_status=doc_status,
        type=type,
        category=category,
        subject=subject,
        author=author,
        custodian=custodian,
        authenticator=authenticator,
        relates_to=relates_to,
        identifier=identifier,
        description=description,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [document_reference_service._to_fhir(d) for d in items],
        [document_reference_service._to_plain(d) for d in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{document_reference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_document_reference",
    summary="Delete a DocumentReference resource",
    description=(
        "Permanently deletes the DocumentReference and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_document_reference(
    document_reference_id: int = Path(
        ..., ge=1, description="Public document_reference identifier."
    ),
    actor: AuthUser = Depends(require_permission("document_reference", "delete")),
    document_reference_service: DocumentReferenceService = Depends(
        get_document_reference_service
    ),
):
    logger.info(
        "Delete a DocumentReference resource",
        extra={
            "event": "route.delete_document_reference",
            "document_reference_id": document_reference_id,
        },
    )
    await document_reference_service.delete_document_reference(
        document_reference_id, org_id=actor.org_id
    )
