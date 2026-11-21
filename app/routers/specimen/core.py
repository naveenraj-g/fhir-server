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
from app.di.dependencies.specimen import get_specimen_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.specimen.search import specimen_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.specimen import (
    SpecimenCreateSchema,
    SpecimenPatchSchema,
)
from app.services.specimen import SpecimenService

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

# Specimen always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_specimen",
    summary="Create a new Specimen resource",
    description=(
        "Records a sample taken from a patient, device, location or other subject — a blood draw, a swab, "
        "a tissue sample — with how it was collected, processed and stored. The request body is a FHIR R4 "
        "Specimen resource (camelCase, nested datatypes — https://www.hl7.org/fhir/R4/specimen.html); every "
        "supplied element (identifier, accessionIdentifier, status, type, subject, receivedTime, parent, "
        "request, collection, processing, container, condition, note) is stored as sent. Every Specimen "
        "element is optional in R4. "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>` or `Location/<id>` subject, `collection.collector` (Practitioner or PractitionerRole), "
        "`parent` (Specimen), a note author and every identifier's `assigner` are rejected with 422 if they do "
        "not exist in the caller's org; a Group, Device or Substance subject, `request` (ServiceRequest), "
        "`processing.additive`, an absolute URL or a logical reference is stored as sent. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_specimen(
    payload: SpecimenCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen", "create")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new Specimen resource",
        extra={"event": "route.create_specimen"},
    )
    log_payload(logger, "specimen.create.payload", payload)
    specimen = await specimen_service.create_specimen(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        specimen_service._to_fhir(specimen),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Specimen search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = specimen_search()
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
    specimen_service: SpecimenService,
):
    search_url, fhir_base = search_urls(request, "search_specimens")
    (
        search_request,
        rows,
        total,
        included,
    ) = await specimen_service.search_specimens(
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
    operation_id="search_specimens",
    summary="Search Specimen resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_specimens(
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen", "read")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Specimen resources",
        extra={"event": "route.search_specimens"},
    )
    return await _search(request, get_query(request), actor, specimen_service)


@router.post(
    "/_search",
    operation_id="search_specimens_post",
    summary="Search Specimen resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_specimens_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen", "read")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    logger.info(
        "Search Specimen resources (POST _search)",
        extra={"event": "route.search_specimens_post"},
    )
    return await _search(request, await post_query(request), actor, specimen_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{specimen_id}",
    operation_id="get_specimen_by_id",
    summary="Retrieve an Specimen resource by public specimen_id",
    description=(
        "Scoped to the caller's own org — get_specimen_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_specimen(
    request: Request,
    specimen_id: int = Path(..., ge=1, description="Public specimen identifier."),
    actor: AuthUser = Depends(require_permission("specimen", "read")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    logger.info(
        "Retrieve an Specimen resource by public specimen_id",
        extra={
            "event": "route.get_specimen_by_id",
            "specimen_id": specimen_id,
        },
    )
    specimen = await specimen_service.get_specimen_scoped(specimen_id, actor.org_id)
    return fhir_response(specimen_service._to_fhir(specimen))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{specimen_id}",
    operation_id="patch_specimen",
    summary="Update a Specimen resource",
    description=(
        "The request body is a partial FHIR R4 Specimen (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, parent, request, processing, container, condition, note — even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `collection` or `type` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_specimen() raises NotFoundError (404, not "
        "403 — avoids leaking that a Specimen with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_specimen(
    payload: SpecimenPatchSchema,
    request: Request,
    specimen_id: int = Path(..., ge=1, description="Public specimen identifier."),
    actor: AuthUser = Depends(require_permission("specimen", "update")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_specimen()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Specimen resource",
        extra={
            "event": "route.patch_specimen",
            "specimen_id": specimen_id,
        },
    )
    log_payload(logger, "specimen.patch.payload", payload)
    updated = await specimen_service.patch_specimen(
        specimen_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(specimen_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{specimen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_specimen",
    summary="Delete an Specimen resource",
    description=(
        "Permanently deletes the Specimen and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "specimen exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_specimen(
    specimen_id: int = Path(..., ge=1, description="Public specimen identifier."),
    actor: AuthUser = Depends(require_permission("specimen", "delete")),
    specimen_service: SpecimenService = Depends(get_specimen_service),
):
    """delete_specimen() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an Specimen resource",
        extra={
            "event": "route.delete_specimen",
            "specimen_id": specimen_id,
        },
    )
    await specimen_service.delete_specimen(specimen_id, org_id=actor.org_id)
