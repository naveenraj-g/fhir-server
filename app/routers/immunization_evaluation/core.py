from fastapi import APIRouter, Depends, Path, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.config import settings
from app.core.content_negotiation import (
    FHIRJSONResponse,
    fhir_response,
    require_fhir_json,
)
from app.core.logging import get_logger, log_payload
from app.di.dependencies.immunization_evaluation import get_immunization_evaluation_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.immunization_evaluation.search import immunization_evaluation_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.immunization_evaluation import ImmunizationEvaluationCreateSchema, ImmunizationEvaluationPatchSchema
from app.services.immunization_evaluation import ImmunizationEvaluationService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_ACCEPTABLE,
    _ERR_NOT_FOUND,
    _ERR_SEARCH,
    _ERR_VALIDATION,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
)

# ImmunizationEvaluation always responds with FHIR R4 JSON, whatever the Accept
# header says (Medplum's approach) — only a client that rules JSON out
# entirely (Accept: application/fhir+xml, _format=xml) gets a 406.
router = APIRouter(
    default_response_class=FHIRJSONResponse,
    dependencies=[Depends(require_fhir_json)],
    responses={**_ERR_NOT_ACCEPTABLE},
)

logger = get_logger(__name__)

# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_immunization_evaluation",
    summary="Create a new ImmunizationEvaluation resource",
    description=(
        "Records the result of evaluating one vaccine administration (an Immunization) against a published "
        "protocol, for a target disease: whether the dose was valid, and why not if it was not. The request body "
        "is a FHIR R4 ImmunizationEvaluation resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/immunizationevaluation.html); every supplied element (identifier, status, "
        "patient, date, authority, targetDisease, immunizationEvent, doseStatus, doseStatusReason, description, "
        "series, doseNumber[x], seriesDoses[x]) is stored as sent. R4 requires `status`, `patient`, "
        "`targetDisease`, `immunizationEvent` and `doseStatus`. "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>`, `Immunization/<id>` (immunizationEvent), `authority` (Organization) and "
        "`identifier.assigner` are rejected with 422 if they do not exist in the caller's org; an absolute URL "
        "or a logical reference is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_immunization_evaluation(
    payload: ImmunizationEvaluationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "create")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(get_immunization_evaluation_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new ImmunizationEvaluation resource",
        extra={"event": "route.create_immunization_evaluation"},
    )
    log_payload(logger, "immunization_evaluation.create.payload", payload)
    immunization_evaluation = await immunization_evaluation_service.create_immunization_evaluation(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        immunization_evaluation_service._to_fhir(immunization_evaluation),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# ImmunizationEvaluation search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = immunization_evaluation_search()
_SEARCH_PARAMETERS = search_parameters(
    _SEARCH_REGISTRY, settings.pagination.max_limit, settings.pagination.default_limit
)
_SEARCH_DESCRIPTION = (
    search_description(_SEARCH_REGISTRY)
    + " Always scoped to the caller's own org (from the verified token) — `org_id` is not a "
    "client-suppliable filter. " + _CONTENT_NEG
)
_FORM_BODY = {
    "required": False,
    "content": {
        "application/x-www-form-urlencoded": {
            "schema": {
                "type": "object",
                "properties": {
                    p["name"]: {**p["schema"], "description": p["description"]}
                    for p in _SEARCH_PARAMETERS
                    if p["in"] == "query"
                },
            }
        }
    },
}


async def _search(
    request: Request,
    query: list[tuple[str, str]],
    actor: AuthUser,
    immunization_evaluation_service: ImmunizationEvaluationService,
):
    search_url, fhir_base = search_urls(request, "search_immunization_evaluations")
    (
        search_request,
        rows,
        total,
        included,
    ) = await immunization_evaluation_service.search_immunization_evaluations(
        query,
        actor.org_id,
        strict=strict_handling(request),
        fhir_base=fhir_base,
    )
    return searchset_response(
        registry=_SEARCH_REGISTRY,
        search_request=search_request,
        search_url=search_url,
        fhir_base=fhir_base,
        rows=rows,
        total=total,
        included=included,
    )


@router.get(
    "/",
    operation_id="search_immunization_evaluations",
    summary="Search ImmunizationEvaluation resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_immunization_evaluations(
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "read")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(get_immunization_evaluation_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search ImmunizationEvaluation resources",
        extra={"event": "route.search_immunization_evaluations"},
    )
    return await _search(request, get_query(request), actor, immunization_evaluation_service)


@router.post(
    "/_search",
    operation_id="search_immunization_evaluations_post",
    summary="Search ImmunizationEvaluation resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_immunization_evaluations_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "read")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(get_immunization_evaluation_service),
):
    logger.info(
        "Search ImmunizationEvaluation resources (POST _search)",
        extra={"event": "route.search_immunization_evaluations_post"},
    )
    return await _search(request, await post_query(request), actor, immunization_evaluation_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{immunization_evaluation_id}",
    operation_id="get_immunization_evaluation_by_id",
    summary="Retrieve an ImmunizationEvaluation resource by public immunization_evaluation_id",
    description=(
        "Scoped to the caller's own org — get_immunization_evaluation_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_immunization_evaluation(
    request: Request,
    immunization_evaluation_id: int = Path(
        ..., ge=1, description="Public immunization_evaluation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "read")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(get_immunization_evaluation_service),
):
    logger.info(
        "Retrieve an ImmunizationEvaluation resource by public immunization_evaluation_id",
        extra={
            "event": "route.get_immunization_evaluation_by_id",
            "immunization_evaluation_id": immunization_evaluation_id,
        },
    )
    immunization_evaluation = await immunization_evaluation_service.get_immunization_evaluation_scoped(
        immunization_evaluation_id, actor.org_id
    )
    return fhir_response(immunization_evaluation_service._to_fhir(immunization_evaluation))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{immunization_evaluation_id}",
    operation_id="patch_immunization_evaluation",
    summary="Update an ImmunizationEvaluation resource",
    description=(
        "The request body is a partial FHIR R4 ImmunizationEvaluation (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, doseStatusReason — even `[]`) atomically replaces the stored entries, a "
        "supplied `patient`, `doseStatus` or `immunizationEvent` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_immunization_evaluation() raises NotFoundError (404, not "
        "403 — avoids leaking that an ImmunizationEvaluation with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_immunization_evaluation(
    payload: ImmunizationEvaluationPatchSchema,
    request: Request,
    immunization_evaluation_id: int = Path(
        ..., ge=1, description="Public immunization_evaluation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "update")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(get_immunization_evaluation_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_immunization_evaluation()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an ImmunizationEvaluation resource",
        extra={"event": "route.patch_immunization_evaluation", "immunization_evaluation_id": immunization_evaluation_id},
    )
    log_payload(logger, "immunization_evaluation.patch.payload", payload)
    updated = await immunization_evaluation_service.patch_immunization_evaluation(
        immunization_evaluation_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(immunization_evaluation_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{immunization_evaluation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_immunization_evaluation",
    summary="Delete an ImmunizationEvaluation resource",
    description=(
        "Permanently deletes the ImmunizationEvaluation and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "immunization_evaluation exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_immunization_evaluation(
    immunization_evaluation_id: int = Path(
        ..., ge=1, description="Public immunization_evaluation identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization_evaluation", "delete")),
    immunization_evaluation_service: ImmunizationEvaluationService = Depends(get_immunization_evaluation_service),
):
    """delete_immunization_evaluation() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an ImmunizationEvaluation resource",
        extra={
            "event": "route.delete_immunization_evaluation",
            "immunization_evaluation_id": immunization_evaluation_id,
        },
    )
    await immunization_evaluation_service.delete_immunization_evaluation(immunization_evaluation_id, org_id=actor.org_id)
