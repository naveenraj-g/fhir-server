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
from app.di.dependencies.goal import get_goal_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.goal.search import goal_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.goal import (
    GoalCreateSchema,
    GoalPatchSchema,
)
from app.services.goal import GoalService

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

# Goal always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_goal",
    summary="Create a new Goal resource",
    description=(
        "Records a goal - a drug product, its form, its ingredients and (for a package) its "
        "batch. The request body is a FHIR R4 Goal resource (camelCase, nested datatypes - "
        "https://www.hl7.org/fhir/R4/goal.html); every supplied element (identifier, code, "
        "status, manufacturer, form, amount, ingredient, batch) is stored as sent. Every Goal "
        "element is optional in R4. The body is checked against base FHIR R4: any valid R4 element is "
        "accepted and stored as sent (server-managed `id`/`meta` are ignored); a key that is not FHIR at "
        "all is rejected with 422. A relative `Organization/<id>` manufacturer, a Goal ingredient "
        "(`ingredient.itemReference`) and every identifier's `assigner` are rejected with 422 if they do "
        "not exist in the caller's org; a Substance ingredient, an absolute URL or a logical reference is "
        "stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_goal(
    payload: GoalCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("goal", "create")),
    goal_service: GoalService = Depends(get_goal_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new Goal resource",
        extra={"event": "route.create_goal"},
    )
    log_payload(logger, "goal.create.payload", payload)
    goal = await goal_service.create_goal(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        goal_service._to_fhir(goal),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Goal search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = goal_search()
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
    goal_service: GoalService,
):
    search_url, fhir_base = search_urls(request, "search_goals")
    (
        search_request,
        rows,
        total,
        included,
    ) = await goal_service.search_goals(
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
    operation_id="search_goals",
    summary="Search Goal resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_goals(
    request: Request,
    actor: AuthUser = Depends(require_permission("goal", "read")),
    goal_service: GoalService = Depends(get_goal_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Goal resources",
        extra={"event": "route.search_goals"},
    )
    return await _search(request, get_query(request), actor, goal_service)


@router.post(
    "/_search",
    operation_id="search_goals_post",
    summary="Search Goal resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_goals_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("goal", "read")),
    goal_service: GoalService = Depends(get_goal_service),
):
    logger.info(
        "Search Goal resources (POST _search)",
        extra={"event": "route.search_goals_post"},
    )
    return await _search(request, await post_query(request), actor, goal_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{goal_id}",
    operation_id="get_goal_by_id",
    summary="Retrieve a Goal resource by public goal_id",
    description=(
        "Scoped to the caller's own org — get_goal_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_goal(
    request: Request,
    goal_id: int = Path(..., ge=1, description="Public goal identifier."),
    actor: AuthUser = Depends(require_permission("goal", "read")),
    goal_service: GoalService = Depends(get_goal_service),
):
    logger.info(
        "Retrieve a Goal resource by public goal_id",
        extra={
            "event": "route.get_goal_by_id",
            "goal_id": goal_id,
        },
    )
    goal = await goal_service.get_goal_scoped(goal_id, actor.org_id)
    return fhir_response(goal_service._to_fhir(goal))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{goal_id}",
    operation_id="patch_goal",
    summary="Update a Goal resource",
    description=(
        "The request body is a partial FHIR R4 Goal (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, ingredient — even `[]`) atomically replaces the stored entries, a "
        "supplied `code`, `batch` or `manufacturer` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_goal() raises NotFoundError (404, not "
        "403 — avoids leaking that a goal with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_goal(
    payload: GoalPatchSchema,
    request: Request,
    goal_id: int = Path(..., ge=1, description="Public goal identifier."),
    actor: AuthUser = Depends(require_permission("goal", "update")),
    goal_service: GoalService = Depends(get_goal_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_goal()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Goal resource",
        extra={
            "event": "route.patch_goal",
            "goal_id": goal_id,
        },
    )
    log_payload(logger, "goal.patch.payload", payload)
    updated = await goal_service.patch_goal(
        goal_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(goal_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_goal",
    summary="Delete a Goal resource",
    description=(
        "Permanently deletes the Goal and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "goal exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_goal(
    goal_id: int = Path(..., ge=1, description="Public goal identifier."),
    actor: AuthUser = Depends(require_permission("goal", "delete")),
    goal_service: GoalService = Depends(get_goal_service),
):
    """delete_goal() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a Goal resource",
        extra={
            "event": "route.delete_goal",
            "goal_id": goal_id,
        },
    )
    await goal_service.delete_goal(goal_id, org_id=actor.org_id)
