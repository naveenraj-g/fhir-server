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
from app.di.dependencies.plan_definition import get_plan_definition_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.plan_definition.search import plan_definition_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.plan_definition import (
    PlanDefinitionCreateSchema,
    PlanDefinitionPatchSchema,
)
from app.services.plan_definition import PlanDefinitionService

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

# PlanDefinition always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_plan_definition",
    summary="Create a new PlanDefinition resource",
    description=(
        "Records a pre-defined group of actions to be taken in particular circumstances (an order set, a clinical protocol, a decision-support rule, ...). "
        "The request body is a FHIR R4 PlanDefinition resource (camelCase, nested datatypes - "
        "https://www.hl7.org/fhir/R4/plandefinition.html); every supplied element (url, identifier, version, name, "
        "title, type, status, experimental, date, publisher, contact, description, useContext, jurisdiction, topic, "
        "relatedArtifact, library, goal and the nested action tree, ...) is stored as sent. R4 requires `status`, which only the "
        "java_validator backend enforces. The body is checked against base FHIR R4: any valid R4 element is "
        "accepted and stored as sent (server-managed `id`/`meta` are ignored); a key that is not FHIR at all is "
        "rejected with 422. A relative reference in `identifier.assigner`, `subjectReference`, "
        "or a `useContext.valueReference` that "
        "names a resource this server has is rejected with 422 if it does not exist in the caller's org; an "
        "absolute URL, a logical reference or a resource type this server does not have is stored as sent. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_plan_definition(
    payload: PlanDefinitionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("plan_definition", "create")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new PlanDefinition resource",
        extra={"event": "route.create_plan_definition"},
    )
    log_payload(logger, "plan_definition.create.payload", payload)
    plan_definition = await plan_definition_service.create_plan_definition(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        plan_definition_service._to_fhir(plan_definition),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# PlanDefinition search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = plan_definition_search()
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
    plan_definition_service: PlanDefinitionService,
):
    search_url, fhir_base = search_urls(request, "search_plan_definitions")
    (
        search_request,
        rows,
        total,
        included,
    ) = await plan_definition_service.search_plan_definitions(
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
    operation_id="search_plan_definitions",
    summary="Search PlanDefinition resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_plan_definitions(
    request: Request,
    actor: AuthUser = Depends(require_permission("plan_definition", "read")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search PlanDefinition resources",
        extra={"event": "route.search_plan_definitions"},
    )
    return await _search(request, get_query(request), actor, plan_definition_service)


@router.post(
    "/_search",
    operation_id="search_plan_definitions_post",
    summary="Search PlanDefinition resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_plan_definitions_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("plan_definition", "read")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    logger.info(
        "Search PlanDefinition resources (POST _search)",
        extra={"event": "route.search_plan_definitions_post"},
    )
    return await _search(
        request, await post_query(request), actor, plan_definition_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{plan_definition_id}",
    operation_id="get_plan_definition_by_id",
    summary="Retrieve a PlanDefinition resource by public plan_definition_id",
    description=(
        "Scoped to the caller's own org — get_plan_definition_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_plan_definition(
    request: Request,
    plan_definition_id: int = Path(
        ..., ge=1, description="Public plan_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("plan_definition", "read")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    logger.info(
        "Retrieve a PlanDefinition resource by public plan_definition_id",
        extra={
            "event": "route.get_plan_definition_by_id",
            "plan_definition_id": plan_definition_id,
        },
    )
    plan_definition = await plan_definition_service.get_plan_definition_scoped(
        plan_definition_id, actor.org_id
    )
    return fhir_response(plan_definition_service._to_fhir(plan_definition))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{plan_definition_id}",
    operation_id="patch_plan_definition",
    summary="Update a PlanDefinition resource",
    description=(
        "The request body is a partial FHIR R4 PlanDefinition (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, contact, useContext, jurisdiction, topic, relatedArtifact, goal, action - even `[]`) atomically replaces "
        "the stored entries, a supplied `effectivePeriod` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_plan_definition() raises NotFoundError (404, not "
        "403 — avoids leaking that a PlanDefinition with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_plan_definition(
    payload: PlanDefinitionPatchSchema,
    request: Request,
    plan_definition_id: int = Path(
        ..., ge=1, description="Public plan_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("plan_definition", "update")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_plan_definition()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a PlanDefinition resource",
        extra={
            "event": "route.patch_plan_definition",
            "plan_definition_id": plan_definition_id,
        },
    )
    log_payload(logger, "plan_definition.patch.payload", payload)
    updated = await plan_definition_service.patch_plan_definition(
        plan_definition_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(plan_definition_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{plan_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_plan_definition",
    summary="Delete a PlanDefinition resource",
    description=(
        "Permanently deletes the PlanDefinition and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "plan_definition exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_plan_definition(
    plan_definition_id: int = Path(
        ..., ge=1, description="Public plan_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("plan_definition", "delete")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    """delete_plan_definition() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a PlanDefinition resource",
        extra={
            "event": "route.delete_plan_definition",
            "plan_definition_id": plan_definition_id,
        },
    )
    await plan_definition_service.delete_plan_definition(
        plan_definition_id, org_id=actor.org_id
    )
