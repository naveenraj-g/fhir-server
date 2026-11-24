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
from app.di.dependencies.medication_knowledge import get_medication_knowledge_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.medication_knowledge.search import medication_knowledge_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.medication_knowledge import (
    MedicationKnowledgeCreateSchema,
    MedicationKnowledgePatchSchema,
)
from app.services.medication_knowledge import MedicationKnowledgeService

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

# MedicationKnowledge always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_medication_knowledge",
    summary="Create a new MedicationKnowledge resource",
    description=(
        "Records a medication_knowledge - a drug product, its form, its ingredients and (for a package) its "
        "batch. The request body is a FHIR R4 MedicationKnowledge resource (camelCase, nested datatypes - "
        "https://www.hl7.org/fhir/R4/medication_knowledge.html); every supplied element (identifier, code, "
        "status, manufacturer, form, amount, ingredient, batch) is stored as sent. Every MedicationKnowledge "
        "element is optional in R4. The body is checked against base FHIR R4: any valid R4 element is "
        "accepted and stored as sent (server-managed `id`/`meta` are ignored); a key that is not FHIR at "
        "all is rejected with 422. A relative `Organization/<id>` manufacturer, a MedicationKnowledge ingredient "
        "(`ingredient.itemReference`) and every identifier's `assigner` are rejected with 422 if they do "
        "not exist in the caller's org; a Substance ingredient, an absolute URL or a logical reference is "
        "stored as sent. " + _CONTENT_NEG
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
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new MedicationKnowledge resource",
        extra={"event": "route.create_medication_knowledge"},
    )
    log_payload(logger, "medication_knowledge.create.payload", payload)
    medication_knowledge = (
        await medication_knowledge_service.create_medication_knowledge(
            payload, actor.org_id, actor.sub, body=await request.json()
        )
    )
    return fhir_response(
        medication_knowledge_service._to_fhir(medication_knowledge),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# MedicationKnowledge search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = medication_knowledge_search()
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
    medication_knowledge_service: MedicationKnowledgeService,
):
    search_url, fhir_base = search_urls(request, "search_medication_knowledge")
    (
        search_request,
        rows,
        total,
        included,
    ) = await medication_knowledge_service.search_medication_knowledge(
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
    operation_id="search_medication_knowledge",
    summary="Search MedicationKnowledge resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_medication_knowledge(
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_knowledge", "read")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search MedicationKnowledge resources",
        extra={"event": "route.search_medication_knowledge"},
    )
    return await _search(
        request, get_query(request), actor, medication_knowledge_service
    )


@router.post(
    "/_search",
    operation_id="search_medication_knowledge_post",
    summary="Search MedicationKnowledge resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_medication_knowledge_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_knowledge", "read")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    logger.info(
        "Search MedicationKnowledge resources (POST _search)",
        extra={"event": "route.search_medication_knowledge_post"},
    )
    return await _search(
        request, await post_query(request), actor, medication_knowledge_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_knowledge_id}",
    operation_id="get_medication_knowledge_by_id",
    summary="Retrieve a MedicationKnowledge resource by public medication_knowledge_id",
    description=(
        "Scoped to the caller's own org — get_medication_knowledge_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication_knowledge(
    request: Request,
    medication_knowledge_id: int = Path(
        ..., ge=1, description="Public medication_knowledge identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_knowledge", "read")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    logger.info(
        "Retrieve a MedicationKnowledge resource by public medication_knowledge_id",
        extra={
            "event": "route.get_medication_knowledge_by_id",
            "medication_knowledge_id": medication_knowledge_id,
        },
    )
    medication_knowledge = (
        await medication_knowledge_service.get_medication_knowledge_scoped(
            medication_knowledge_id, actor.org_id
        )
    )
    return fhir_response(medication_knowledge_service._to_fhir(medication_knowledge))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{medication_knowledge_id}",
    operation_id="patch_medication_knowledge",
    summary="Update a MedicationKnowledge resource",
    description=(
        "The request body is a partial FHIR R4 MedicationKnowledge (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, ingredient — even `[]`) atomically replaces the stored entries, a "
        "supplied `code`, `batch` or `manufacturer` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_medication_knowledge() raises NotFoundError (404, not "
        "403 — avoids leaking that a medication_knowledge with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_knowledge(
    payload: MedicationKnowledgePatchSchema,
    request: Request,
    medication_knowledge_id: int = Path(
        ..., ge=1, description="Public medication_knowledge identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_knowledge", "update")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_medication_knowledge()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a MedicationKnowledge resource",
        extra={
            "event": "route.patch_medication_knowledge",
            "medication_knowledge_id": medication_knowledge_id,
        },
    )
    log_payload(logger, "medication_knowledge.patch.payload", payload)
    updated = await medication_knowledge_service.patch_medication_knowledge(
        medication_knowledge_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(medication_knowledge_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{medication_knowledge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_medication_knowledge",
    summary="Delete a MedicationKnowledge resource",
    description=(
        "Permanently deletes the MedicationKnowledge and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "medication_knowledge exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_medication_knowledge(
    medication_knowledge_id: int = Path(
        ..., ge=1, description="Public medication_knowledge identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_knowledge", "delete")),
    medication_knowledge_service: MedicationKnowledgeService = Depends(
        get_medication_knowledge_service
    ),
):
    """delete_medication_knowledge() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a MedicationKnowledge resource",
        extra={
            "event": "route.delete_medication_knowledge",
            "medication_knowledge_id": medication_knowledge_id,
        },
    )
    await medication_knowledge_service.delete_medication_knowledge(
        medication_knowledge_id, org_id=actor.org_id
    )
