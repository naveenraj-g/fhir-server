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
from app.di.dependencies.location import get_location_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.location.search import location_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.location import LocationCreateSchema, LocationPatchSchema
from app.services.location import LocationService

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

# Location always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_location",
    summary="Create a new Location resource",
    description=(
        "Records details and position information for a physical place where services are "
        "provided and resources and participants may be stored, found, contained, or "
        "accommodated. The request body is a FHIR R4 Location resource (camelCase, nested "
        "datatypes — https://www.hl7.org/fhir/R4/location.html), stored atomically in one DB "
        "transaction. The body is checked against base FHIR R4: any valid R4 element is accepted "
        "and stored as sent (server-managed `id`/`meta` are ignored); a key that isn't FHIR at all "
        "is rejected with 422. `managingOrganization` (`Organization/<id>`), `partOf` "
        "(`Location/<id>`) and `identifier.assigner` relative references must exist in the caller's "
        "org (422 otherwise); absolute URLs are stored without a check. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_location(
    payload: LocationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("location", "create")),
    location_service: LocationService = Depends(get_location_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). Location has no user_id
    field at all."""
    logger.info(
        "Create a new Location resource",
        extra={"event": "route.create_location"},
    )
    log_payload(logger, "location.create.payload", payload)
    loc = await location_service.create_location(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        location_service._to_fhir(loc), status_code=status.HTTP_201_CREATED
    )


@router.get(
    "/{location_id}",
    operation_id="get_location_by_id",
    summary="Retrieve a Location resource by public location_id",
    description=(
        "Scoped to the caller's own org — get_location_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_location(
    request: Request,
    location_id: int = Path(
        ..., ge=1, description="Public location identifier."
    ),
    actor: AuthUser = Depends(require_permission("location", "read")),
    location_service: LocationService = Depends(get_location_service),
):
    logger.info(
        "Retrieve a Location resource by public location_id",
        extra={
            "event": "route.get_location_by_id",
            "location_id": location_id,
        },
    )
    loc = await location_service.get_location_scoped(
        location_id, actor.org_id
    )
    return fhir_response(location_service._to_fhir(loc))


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{location_id}",
    operation_id="patch_location",
    summary="Update a Location resource",
    description=(
        "The request body is a partial FHIR R4 Location (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied "
        "list (identifier, type, alias, telecom, hoursOfOperation, endpoint — even `[]`) replaces "
        "the stored entries; a supplied object (`address`, `position`, `managingOrganization`, "
        "`partOf`, ...) replaces the whole element, and `null` clears it. Rejected with 422 if a "
        "referenced Organization/Location doesn't exist, or if `partOf` would create a circular "
        "hierarchy. "
        "Scoped to the caller's own org — patch_location() raises NotFoundError (404, not "
        "403 — avoids leaking that a location with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_location(
    payload: LocationPatchSchema,
    request: Request,
    location_id: int = Path(
        ..., ge=1, description="Public location identifier."
    ),
    actor: AuthUser = Depends(require_permission("location", "update")),
    location_service: LocationService = Depends(get_location_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_location()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Location resource",
        extra={"event": "route.patch_location", "location_id": location_id},
    )
    log_payload(logger, "location.patch.payload", payload)
    updated = await location_service.patch_location(
        location_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(location_service._to_fhir(updated))


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains (`partof.name`) and repeat for AND, none
# of which fit FastAPI's per-name Query() declarations — and validated
# against the Location search registry. The OpenAPI parameter list is
# generated from that same registry.

_SEARCH_REGISTRY = location_search()
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
    location_service: LocationService,
):
    search_url, fhir_base = search_urls(request, "search_locations")
    search_request, rows, total, included = await location_service.search_locations(
        query, actor.org_id, strict=strict_handling(request), fhir_base=fhir_base
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
    operation_id="search_locations",
    summary="Search Location resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_locations(
    request: Request,
    actor: AuthUser = Depends(require_permission("location", "read")),
    location_service: LocationService = Depends(get_location_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Location resources",
        extra={"event": "route.search_locations"},
    )
    return await _search(request, get_query(request), actor, location_service)


@router.post(
    "/_search",
    operation_id="search_locations_post",
    summary="Search Location resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_locations_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("location", "read")),
    location_service: LocationService = Depends(get_location_service),
):
    logger.info(
        "Search Location resources (POST _search)",
        extra={"event": "route.search_locations_post"},
    )
    return await _search(request, await post_query(request), actor, location_service)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_location",
    summary="Delete a Location resource",
    description=(
        "Permanently deletes the Location (and its search-index rows). "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "location exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_location(
    location_id: int = Path(
        ..., ge=1, description="Public location identifier."
    ),
    actor: AuthUser = Depends(require_permission("location", "delete")),
    location_service: LocationService = Depends(get_location_service),
):
    """delete_location() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org. Delete
    cascades to the search-index rows."""
    logger.info(
        "Delete a Location resource",
        extra={
            "event": "route.delete_location",
            "location_id": location_id,
        },
    )
    await location_service.delete_location(location_id, org_id=actor.org_id)
