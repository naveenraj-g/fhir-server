from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.questionnaire_response import get_questionnaire_response_service
from app.schemas.enums import QuestionnaireResponseStatus
from app.schemas.questionnaire_response import (
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
)
from app.services.questionnaire_response import QuestionnaireResponseService

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
    operation_id="create_questionnaire_response",
    summary="Create a new QuestionnaireResponse resource",
    description=(
        "A set of answers to a set of questions, generally the result of completing a "
        "Questionnaire. Accepts the full nested payload — identifier, basedOn, partOf, "
        "and the recursive item/answer tree — atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) "
        "— an org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_questionnaire_response(
    payload: QuestionnaireResponseCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire_response", "create")),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). `user_id` is still a plain
    request body field."""
    logger.info(
        "Create a new QuestionnaireResponse resource",
        extra={"event": "route.create_questionnaire_response"},
    )
    log_payload(logger, "questionnaire_response.create.payload", payload)
    questionnaire_response = await questionnaire_response_service.create_questionnaire_response(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        questionnaire_response_service._to_fhir(questionnaire_response),
        questionnaire_response_service._to_plain(questionnaire_response),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Me (must come before /{questionnaire_response_id}) ──────────────────────────


@router.get(
    "/me",
    operation_id="list_my_questionnaire_responses",
    summary="List QuestionnaireResponse resources owned by the authenticated end-user",
    description=(
        "Same filters as `GET /`, always additionally scoped to the authenticated "
        "end-user's own `user_id` (from the gateway-forwarded field at create time), on "
        "top of the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_questionnaire_responses(
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire_response", "read")),
    questionnaire_response_status: QuestionnaireResponseStatus | None = Query(
        None, alias="status", description="in-progress | completed | amended | entered-in-error | stopped."
    ),
    questionnaire: str | None = Query(None, description="Exact match on the canonical Questionnaire reference."),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    logger.info(
        "List QuestionnaireResponse resources owned by the authenticated end-user",
        extra={"event": "route.list_my_questionnaire_responses"},
    )
    items, total = await questionnaire_response_service.get_me(
        user_id=actor.sub,
        org_id=actor.org_id,
        status=questionnaire_response_status,
        questionnaire=questionnaire,
        subject=subject,
        identifier=identifier,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [questionnaire_response_service._to_fhir(qr) for qr in items],
        [questionnaire_response_service._to_plain(qr) for qr in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{questionnaire_response_id}",
    operation_id="get_questionnaire_response_by_id",
    summary="Retrieve a QuestionnaireResponse resource by public questionnaire_response_id",
    description=(
        "Scoped to the caller's own org — get_questionnaire_response_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_questionnaire_response(
    request: Request,
    questionnaire_response_id: int = Path(..., ge=1, description="Public questionnaire_response identifier."),
    actor: AuthUser = Depends(require_permission("questionnaire_response", "read")),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    logger.info(
        "Retrieve a QuestionnaireResponse resource by public questionnaire_response_id",
        extra={
            "event": "route.get_questionnaire_response_by_id",
            "questionnaire_response_id": questionnaire_response_id,
        },
    )
    questionnaire_response = await questionnaire_response_service.get_questionnaire_response_scoped(
        questionnaire_response_id, actor.org_id
    )
    return format_response(
        questionnaire_response_service._to_fhir(questionnaire_response),
        questionnaire_response_service._to_plain(questionnaire_response),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{questionnaire_response_id}",
    operation_id="patch_questionnaire_response",
    summary="Update a QuestionnaireResponse resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (identifier, basedOn, partOf, item — even `[]`) "
        "atomically replaces the corresponding rows; omitted lists are left untouched. "
        "Scoped to the caller's own org — patch_questionnaire_response() raises "
        "NotFoundError (404, not 403 — avoids leaking that a resource with this id "
        "exists in another org) if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_questionnaire_response(
    payload: QuestionnaireResponsePatchSchema,
    request: Request,
    questionnaire_response_id: int = Path(..., ge=1, description="Public questionnaire_response identifier."),
    actor: AuthUser = Depends(require_permission("questionnaire_response", "update")),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub);
    patch_questionnaire_response() raises NotFoundError (404, not 403) if
    actor.org_id doesn't match."""
    logger.info(
        "Update a QuestionnaireResponse resource",
        extra={
            "event": "route.patch_questionnaire_response",
            "questionnaire_response_id": questionnaire_response_id,
        },
    )
    log_payload(logger, "questionnaire_response.patch.payload", payload)
    updated = await questionnaire_response_service.patch_questionnaire_response(
        questionnaire_response_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        questionnaire_response_service._to_fhir(updated),
        questionnaire_response_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_questionnaire_responses",
    summary="List all QuestionnaireResponse resources",
    description=(
        "Returns a paginated list of QuestionnaireResponse resources, matching a subset "
        "of the search parameters documented at "
        "https://www.hl7.org/fhir/R4/questionnaireresponse.html#search. Filter by "
        "`status`, `questionnaire`/`subject` (exact), `identifier` (exact business-"
        "identifier value). Always scoped to the caller's own org (from the verified "
        "token) — `org_id` is not a client-suppliable filter. Sort with `sort` (e.g. "
        "`-created_at`); set `total_mode=none` to skip the COUNT(*) on large result "
        "sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_questionnaire_responses(
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire_response", "read")),
    questionnaire_response_status: QuestionnaireResponseStatus | None = Query(
        None, alias="status", description="in-progress | completed | amended | entered-in-error | stopped."
    ),
    questionnaire: str | None = Query(None, description="Exact match on the canonical Questionnaire reference."),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; list_questionnaire_responses() raises
    PermissionDeniedError (403) outright for an org-less token."""
    logger.info(
        "List all QuestionnaireResponse resources",
        extra={"event": "route.list_questionnaire_responses"},
    )
    items, total = await questionnaire_response_service.list_questionnaire_responses(
        org_id=actor.org_id,
        status=questionnaire_response_status,
        questionnaire=questionnaire,
        subject=subject,
        identifier=identifier,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [questionnaire_response_service._to_fhir(qr) for qr in items],
        [questionnaire_response_service._to_plain(qr) for qr in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{questionnaire_response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_questionnaire_response",
    summary="Delete a QuestionnaireResponse resource",
    description=(
        "Permanently deletes the QuestionnaireResponse and all associated "
        "sub-resources, including the entire item/answer tree. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if the resource exists but "
        "belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_questionnaire_response(
    questionnaire_response_id: int = Path(..., ge=1, description="Public questionnaire_response identifier."),
    actor: AuthUser = Depends(require_permission("questionnaire_response", "delete")),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    """delete_questionnaire_response() raises NotFoundError (404) if the id
    doesn't exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a QuestionnaireResponse resource",
        extra={
            "event": "route.delete_questionnaire_response",
            "questionnaire_response_id": questionnaire_response_id,
        },
    )
    await questionnaire_response_service.delete_questionnaire_response(
        questionnaire_response_id, org_id=actor.org_id
    )
