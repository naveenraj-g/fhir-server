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
from app.di.dependencies.healthcare_service import get_healthcare_service_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.healthcare_service.search import healthcare_service_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.healthcare_service import HealthcareServiceCreateSchema, HealthcareServicePatchSchema
from app.services.healthcare_service import HealthcareServiceService

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

# HealthcareService always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_healthcare_service",
    summary="Create a new HealthcareService resource",
    description=(
        "Records the details of a healthcare service available at a location, or by an "
        "organization, for a certain type of patient. The request body is a FHIR R4 "
        "HealthcareService resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/healthcareservice.html); the service and every supplied "
        "element (identifier, category, type, specialty, location, telecom, coverageArea, "
        "eligibility, program, characteristic, communication, availableTime, notAvailable, "
        "endpoint, ...) are written atomically in one DB transaction. The body is checked "
        "against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that isn't FHIR at all is rejected "
        "with 422. `providedBy` may reference an Organization and `location` / `coverageArea` "
        "a Location (e.g. `{\"reference\": \"Location/230001\"}`) — rejected with 422 if the "
        "referenced resource doesn't exist in the caller's org. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_healthcare_service(
    payload: HealthcareServiceCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("healthcare_service", "create")),
    healthcare_service_service: HealthcareServiceService = Depends(get_healthcare_service_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new HealthcareService resource",
        extra={"event": "route.create_healthcare_service"},
    )
    log_payload(logger, "healthcare_service.create.payload", payload)
    healthcare_service = await healthcare_service_service.create_healthcare_service(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        healthcare_service_service._to_fhir(healthcare_service),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# HealthcareService search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = healthcare_service_search()
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
    healthcare_service_service: HealthcareServiceService,
):
    search_url, fhir_base = search_urls(request, "search_healthcare_services")
    (
        search_request,
        rows,
        total,
        included,
    ) = await healthcare_service_service.search_healthcare_services(
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
    operation_id="search_healthcare_services",
    summary="Search HealthcareService resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_healthcare_services(
    request: Request,
    actor: AuthUser = Depends(require_permission("healthcare_service", "read")),
    healthcare_service_service: HealthcareServiceService = Depends(get_healthcare_service_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search HealthcareService resources",
        extra={"event": "route.search_healthcare_services"},
    )
    return await _search(request, get_query(request), actor, healthcare_service_service)


@router.post(
    "/_search",
    operation_id="search_healthcare_services_post",
    summary="Search HealthcareService resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_healthcare_services_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("healthcare_service", "read")),
    healthcare_service_service: HealthcareServiceService = Depends(get_healthcare_service_service),
):
    logger.info(
        "Search HealthcareService resources (POST _search)",
        extra={"event": "route.search_healthcare_services_post"},
    )
    return await _search(request, await post_query(request), actor, healthcare_service_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{healthcare_service_id}",
    operation_id="get_healthcare_service_by_id",
    summary="Retrieve a HealthcareService resource by public healthcare_service_id",
    description=(
        "Scoped to the caller's own org — get_healthcare_service_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_healthcare_service(
    request: Request,
    healthcare_service_id: int = Path(
        ..., ge=1, description="Public healthcare_service identifier."
    ),
    actor: AuthUser = Depends(require_permission("healthcare_service", "read")),
    healthcare_service_service: HealthcareServiceService = Depends(get_healthcare_service_service),
):
    logger.info(
        "Retrieve a HealthcareService resource by public healthcare_service_id",
        extra={
            "event": "route.get_healthcare_service_by_id",
            "healthcare_service_id": healthcare_service_id,
        },
    )
    healthcare_service = await healthcare_service_service.get_healthcare_service_scoped(
        healthcare_service_id, actor.org_id
    )
    return fhir_response(healthcare_service_service._to_fhir(healthcare_service))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{healthcare_service_id}",
    operation_id="patch_healthcare_service",
    summary="Update a HealthcareService resource",
    description=(
        "The request body is a partial FHIR R4 HealthcareService (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. Every supplied "
        "list (identifier, category, type, specialty, location, telecom, coverageArea, eligibility, "
        "program, characteristic, availableTime, notAvailable, endpoint, ... — even `[]`) atomically "
        "replaces the stored entries, a supplied `providedBy` replaces the whole Reference, and `null` "
        "clears an element. "
        "Scoped to the caller's own org — patch_healthcare_service() raises NotFoundError (404, not "
        "403 — avoids leaking that a healthcare_service with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_healthcare_service(
    payload: HealthcareServicePatchSchema,
    request: Request,
    healthcare_service_id: int = Path(
        ..., ge=1, description="Public healthcare_service identifier."
    ),
    actor: AuthUser = Depends(require_permission("healthcare_service", "update")),
    healthcare_service_service: HealthcareServiceService = Depends(get_healthcare_service_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_healthcare_service()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a HealthcareService resource",
        extra={"event": "route.patch_healthcare_service", "healthcare_service_id": healthcare_service_id},
    )
    log_payload(logger, "healthcare_service.patch.payload", payload)
    updated = await healthcare_service_service.patch_healthcare_service(
        healthcare_service_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(healthcare_service_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{healthcare_service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_healthcare_service",
    summary="Delete a HealthcareService resource",
    description=(
        "Permanently deletes the HealthcareService and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "healthcare_service exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_healthcare_service(
    healthcare_service_id: int = Path(
        ..., ge=1, description="Public healthcare_service identifier."
    ),
    actor: AuthUser = Depends(require_permission("healthcare_service", "delete")),
    healthcare_service_service: HealthcareServiceService = Depends(get_healthcare_service_service),
):
    """delete_healthcare_service() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a HealthcareService resource",
        extra={
            "event": "route.delete_healthcare_service",
            "healthcare_service_id": healthcare_service_id,
        },
    )
    await healthcare_service_service.delete_healthcare_service(healthcare_service_id, org_id=actor.org_id)
