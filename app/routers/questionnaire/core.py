from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.questionnaire import get_questionnaire_service
from app.schemas.enums import QuestionnaireStatus
from app.schemas.questionnaire import QuestionnaireCreateSchema, QuestionnairePatchSchema
from app.services.questionnaire import QuestionnaireService

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
    operation_id="create_questionnaire",
    summary="Create a new Questionnaire resource",
    description=(
        "A structured set of questions intended to guide the collection of answers. "
        "Accepts the full nested payload — identifier, contact, useContext, jurisdiction, "
        "code, and the recursive item tree — atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) "
        "— an org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_questionnaire(
    payload: QuestionnaireCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire", "create")),
    questionnaire_service: QuestionnaireService = Depends(get_questionnaire_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). `user_id`, like Practitioner's,
    is still a plain request body field."""
    logger.info(
        "Create a new Questionnaire resource",
        extra={"event": "route.create_questionnaire"},
    )
    log_payload(logger, "questionnaire.create.payload", payload)
    questionnaire = await questionnaire_service.create_questionnaire(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        questionnaire_service._to_fhir(questionnaire),
        questionnaire_service._to_plain(questionnaire),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Me (must come before /{questionnaire_id}) ───────────────────────────────────


@router.get(
    "/me",
    operation_id="list_my_questionnaires",
    summary="List Questionnaire resources owned by the authenticated end-user",
    description=(
        "Same filters as `GET /`, always additionally scoped to the authenticated "
        "end-user's own `user_id` (from the gateway-forwarded field at create time), on "
        "top of the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_questionnaires(
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire", "read")),
    questionnaire_status: QuestionnaireStatus | None = Query(
        None, alias="status", description="draft | active | retired | unknown."
    ),
    url: str | None = Query(None, description="Exact match on the canonical url."),
    name: str | None = Query(None, description="Substring match on name."),
    title: str | None = Query(None, description="Substring match on title."),
    publisher: str | None = Query(None, description="Substring match on publisher."),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    params: ListParams = Depends(),
    questionnaire_service: QuestionnaireService = Depends(get_questionnaire_service),
):
    logger.info(
        "List Questionnaire resources owned by the authenticated end-user",
        extra={"event": "route.list_my_questionnaires"},
    )
    items, total = await questionnaire_service.get_me(
        user_id=actor.sub,
        org_id=actor.org_id,
        status=questionnaire_status,
        url=url,
        name=name,
        title=title,
        publisher=publisher,
        identifier=identifier,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [questionnaire_service._to_fhir(q) for q in items],
        [questionnaire_service._to_plain(q) for q in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{questionnaire_id}",
    operation_id="get_questionnaire_by_id",
    summary="Retrieve a Questionnaire resource by public questionnaire_id",
    description=(
        "Scoped to the caller's own org — get_questionnaire_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_questionnaire(
    request: Request,
    questionnaire_id: int = Path(..., ge=1, description="Public questionnaire identifier."),
    actor: AuthUser = Depends(require_permission("questionnaire", "read")),
    questionnaire_service: QuestionnaireService = Depends(get_questionnaire_service),
):
    logger.info(
        "Retrieve a Questionnaire resource by public questionnaire_id",
        extra={"event": "route.get_questionnaire_by_id", "questionnaire_id": questionnaire_id},
    )
    questionnaire = await questionnaire_service.get_questionnaire_scoped(
        questionnaire_id, actor.org_id
    )
    return format_response(
        questionnaire_service._to_fhir(questionnaire),
        questionnaire_service._to_plain(questionnaire),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{questionnaire_id}",
    operation_id="patch_questionnaire",
    summary="Update a Questionnaire resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (identifier, contact, useContext, jurisdiction, code, "
        "item — even `[]`) atomically replaces the corresponding rows; omitted lists are "
        "left untouched. Scoped to the caller's own org — patch_questionnaire() raises "
        "NotFoundError (404, not 403 — avoids leaking that a questionnaire with this id "
        "exists in another org) if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_questionnaire(
    payload: QuestionnairePatchSchema,
    request: Request,
    questionnaire_id: int = Path(..., ge=1, description="Public questionnaire identifier."),
    actor: AuthUser = Depends(require_permission("questionnaire", "update")),
    questionnaire_service: QuestionnaireService = Depends(get_questionnaire_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_questionnaire()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Questionnaire resource",
        extra={"event": "route.patch_questionnaire", "questionnaire_id": questionnaire_id},
    )
    log_payload(logger, "questionnaire.patch.payload", payload)
    updated = await questionnaire_service.patch_questionnaire(
        questionnaire_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        questionnaire_service._to_fhir(updated),
        questionnaire_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_questionnaires",
    summary="List all Questionnaire resources",
    description=(
        "Returns a paginated list of Questionnaire resources, matching the search "
        "parameter set documented at https://www.hl7.org/fhir/R4/questionnaire.html#search. "
        "Filter by `status`, `url` (exact), `name`/`title`/`publisher` (substring), "
        "`identifier` (exact business-identifier value). Always scoped to the caller's own "
        "org (from the verified token) — `org_id` is not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-created_at`); set `total_mode=none` to skip the "
        "COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_questionnaires(
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire", "read")),
    questionnaire_status: QuestionnaireStatus | None = Query(
        None, alias="status", description="draft | active | retired | unknown."
    ),
    url: str | None = Query(None, description="Exact match on the canonical url."),
    name: str | None = Query(None, description="Substring match on name."),
    title: str | None = Query(None, description="Substring match on title."),
    publisher: str | None = Query(None, description="Substring match on publisher."),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    params: ListParams = Depends(),
    questionnaire_service: QuestionnaireService = Depends(get_questionnaire_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; list_questionnaires() raises PermissionDeniedError
    (403) outright for an org-less token."""
    logger.info(
        "List all Questionnaire resources",
        extra={"event": "route.list_questionnaires"},
    )
    items, total = await questionnaire_service.list_questionnaires(
        org_id=actor.org_id,
        status=questionnaire_status,
        url=url,
        name=name,
        title=title,
        publisher=publisher,
        identifier=identifier,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [questionnaire_service._to_fhir(q) for q in items],
        [questionnaire_service._to_plain(q) for q in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{questionnaire_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_questionnaire",
    summary="Delete a Questionnaire resource",
    description=(
        "Permanently deletes the Questionnaire and all associated sub-resources, "
        "including the entire item tree. Scoped to the caller's own org — raises "
        "NotFoundError (404, not 403) if the questionnaire exists but belongs to a "
        "different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_questionnaire(
    questionnaire_id: int = Path(..., ge=1, description="Public questionnaire identifier."),
    actor: AuthUser = Depends(require_permission("questionnaire", "delete")),
    questionnaire_service: QuestionnaireService = Depends(get_questionnaire_service),
):
    """delete_questionnaire() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a Questionnaire resource",
        extra={"event": "route.delete_questionnaire", "questionnaire_id": questionnaire_id},
    )
    await questionnaire_service.delete_questionnaire(questionnaire_id, org_id=actor.org_id)
