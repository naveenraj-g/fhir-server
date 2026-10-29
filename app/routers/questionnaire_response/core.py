from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.deps.questionnaire_response_deps import resolve_questionnaire_response
from app.di.dependencies.questionnaire_response import get_questionnaire_response_service
from app.models.questionnaire_response import QuestionnaireResponseModel
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
        "and the recursive item/answer tree — atomically in one DB transaction. Default "
        "(gateway-trusted) pattern: `tenant_id`/`created_by` are plain request body "
        "fields, not derived from a verified JWT. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_questionnaire_response(
    payload: QuestionnaireResponseCreateSchema,
    request: Request,
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    logger.info(
        "Create a new QuestionnaireResponse resource",
        extra={"event": "route.create_questionnaire_response"},
    )
    log_payload(logger, "questionnaire_response.create.payload", payload)
    questionnaire_response = await questionnaire_response_service.create_questionnaire_response(payload)
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
    summary="List QuestionnaireResponse resources owned by a given end-user",
    description=(
        "Same filters as `GET /`, scoped to the gateway-forwarded `user_id` query "
        "param (default/gateway-trusted pattern — not derived from a verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_questionnaire_responses(
    request: Request,
    user_id: str = Query(..., description="Gateway-forwarded ID of the end-user to scope results to."),
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID."),
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
        "List QuestionnaireResponse resources owned by a given end-user",
        extra={"event": "route.list_my_questionnaire_responses"},
    )
    items, total = await questionnaire_response_service.get_me(
        user_id=user_id,
        tenant_id=tenant_id,
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
        "Loaded via `resolve_questionnaire_response()` — a plain load-by-public-ID "
        "lookup with no ownership check (default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_questionnaire_response(
    request: Request,
    questionnaire_response: QuestionnaireResponseModel = Depends(resolve_questionnaire_response),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    logger.info(
        "Retrieve a QuestionnaireResponse resource by public questionnaire_response_id",
        extra={
            "event": "route.get_questionnaire_response_by_id",
            "questionnaire_response_id": questionnaire_response.questionnaire_response_id,
        },
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
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_questionnaire_response(
    payload: QuestionnaireResponsePatchSchema,
    request: Request,
    questionnaire_response_id: int = Path(..., ge=1, description="Public questionnaire_response identifier."),
    _existing: QuestionnaireResponseModel = Depends(resolve_questionnaire_response),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    logger.info(
        "Update a QuestionnaireResponse resource",
        extra={
            "event": "route.patch_questionnaire_response",
            "questionnaire_response_id": questionnaire_response_id,
        },
    )
    log_payload(logger, "questionnaire_response.patch.payload", payload)
    updated = await questionnaire_response_service.patch_questionnaire_response(
        questionnaire_response_id, payload
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
        "identifier value), plus `tenant_id`/`user_id` as explicit, gateway-forwarded "
        "query filters (default/gateway-trusted pattern — neither is derived from a "
        "token). Sort with `sort` (e.g. `-created_at`); set `total_mode=none` to skip "
        "the COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_questionnaire_responses(
    request: Request,
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID filter."),
    user_id: str | None = Query(None, description="Gateway-forwarded end-user ID filter."),
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
        "List all QuestionnaireResponse resources",
        extra={"event": "route.list_questionnaire_responses"},
    )
    items, total = await questionnaire_response_service.list_questionnaire_responses(
        tenant_id=tenant_id,
        user_id=user_id,
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
        "sub-resources, including the entire item/answer tree. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_questionnaire_response(
    questionnaire_response_id: int = Path(..., ge=1, description="Public questionnaire_response identifier."),
    _existing: QuestionnaireResponseModel = Depends(resolve_questionnaire_response),
    questionnaire_response_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    logger.info(
        "Delete a QuestionnaireResponse resource",
        extra={
            "event": "route.delete_questionnaire_response",
            "questionnaire_response_id": questionnaire_response_id,
        },
    )
    await questionnaire_response_service.delete_questionnaire_response(questionnaire_response_id)
