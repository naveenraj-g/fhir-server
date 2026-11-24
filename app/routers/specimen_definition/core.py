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
from app.di.dependencies.specimen_definition import (
    get_specimen_definition_service,
)
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.specimen_definition.search import specimen_definition_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.specimen_definition import (
    SpecimenDefinitionCreateSchema,
    SpecimenDefinitionPatchSchema,
)
from app.services.specimen_definition import SpecimenDefinitionService

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

# SpecimenDefinition always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_specimen_definition",
    summary="Create a new SpecimenDefinition resource",
    description=(
        "Records the kind of specimen a lab collects and tests: the material to collect, patient preparation, collection method and, per tested specimen, its container, retention time, rejection criteria and handling. "
        "The request body is a FHIR R4 SpecimenDefinition resource (camelCase, nested datatypes - "
        "https://www.hl7.org/fhir/R4/specimendefinition.html); every supplied element (identifier, typeCollected, "
        "patientPreparation, timeAspect, collection, typeTested, ...) is stored as sent. R4 has no required top-level "
        "element; each typeTested needs its `preference`, which only the "
        "java_validator backend enforces. The body is checked against base FHIR R4: any valid R4 element is "
        "accepted and stored as sent (server-managed `id`/`meta` are ignored); a key that is not FHIR at all is "
        "rejected with 422. A relative reference in `identifier.assigner` or a container additive "
        "that "
        "names a resource this server has is rejected with 422 if it does not exist in the caller's org; an "
        "absolute URL, a logical reference or a resource type this server does not have is stored as sent. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_specimen_definition(
    payload: SpecimenDefinitionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen_definition", "create")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new SpecimenDefinition resource",
        extra={"event": "route.create_specimen_definition"},
    )
    log_payload(logger, "specimen_definition.create.payload", payload)
    specimen_definition = await specimen_definition_service.create_specimen_definition(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        specimen_definition_service._to_fhir(specimen_definition),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# SpecimenDefinition search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = specimen_definition_search()
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
    specimen_definition_service: SpecimenDefinitionService,
):
    search_url, fhir_base = search_urls(request, "search_specimen_definitions")
    (
        search_request,
        rows,
        total,
        included,
    ) = await specimen_definition_service.search_specimen_definitions(
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
    operation_id="search_specimen_definitions",
    summary="Search SpecimenDefinition resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_specimen_definitions(
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen_definition", "read")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search SpecimenDefinition resources",
        extra={"event": "route.search_specimen_definitions"},
    )
    return await _search(
        request, get_query(request), actor, specimen_definition_service
    )


@router.post(
    "/_search",
    operation_id="search_specimen_definitions_post",
    summary="Search SpecimenDefinition resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_specimen_definitions_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen_definition", "read")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    logger.info(
        "Search SpecimenDefinition resources (POST _search)",
        extra={"event": "route.search_specimen_definitions_post"},
    )
    return await _search(
        request, await post_query(request), actor, specimen_definition_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{specimen_definition_id}",
    operation_id="get_specimen_definition_by_id",
    summary="Retrieve an SpecimenDefinition resource by public specimen_definition_id",
    description=(
        "Scoped to the caller's own org — get_specimen_definition_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_specimen_definition(
    request: Request,
    specimen_definition_id: int = Path(
        ..., ge=1, description="Public specimen_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("specimen_definition", "read")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    logger.info(
        "Retrieve an SpecimenDefinition resource by public specimen_definition_id",
        extra={
            "event": "route.get_specimen_definition_by_id",
            "specimen_definition_id": specimen_definition_id,
        },
    )
    specimen_definition = (
        await specimen_definition_service.get_specimen_definition_scoped(
            specimen_definition_id, actor.org_id
        )
    )
    return fhir_response(specimen_definition_service._to_fhir(specimen_definition))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{specimen_definition_id}",
    operation_id="patch_specimen_definition",
    summary="Update an SpecimenDefinition resource",
    description=(
        "The request body is a partial FHIR R4 SpecimenDefinition (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(patientPreparation, collection, typeTested - even `[]`) atomically replaces "
        "the stored entries, a supplied object (`identifier`, `typeCollected`, ...) replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_specimen_definition() raises NotFoundError (404, not "
        "403 — avoids leaking that an SpecimenDefinition with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_specimen_definition(
    payload: SpecimenDefinitionPatchSchema,
    request: Request,
    specimen_definition_id: int = Path(
        ..., ge=1, description="Public specimen_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("specimen_definition", "update")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_specimen_definition()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an SpecimenDefinition resource",
        extra={
            "event": "route.patch_specimen_definition",
            "specimen_definition_id": specimen_definition_id,
        },
    )
    log_payload(logger, "specimen_definition.patch.payload", payload)
    updated = await specimen_definition_service.patch_specimen_definition(
        specimen_definition_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(specimen_definition_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{specimen_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_specimen_definition",
    summary="Delete an SpecimenDefinition resource",
    description=(
        "Permanently deletes the SpecimenDefinition and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "specimen_definition exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_specimen_definition(
    specimen_definition_id: int = Path(
        ..., ge=1, description="Public specimen_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("specimen_definition", "delete")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    """delete_specimen_definition() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an SpecimenDefinition resource",
        extra={
            "event": "route.delete_specimen_definition",
            "specimen_definition_id": specimen_definition_id,
        },
    )
    await specimen_definition_service.delete_specimen_definition(
        specimen_definition_id, org_id=actor.org_id
    )
