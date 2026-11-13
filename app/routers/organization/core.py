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
from app.di.dependencies.organization import get_organization_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.organization.search import organization_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.organization import OrganizationCreateSchema, OrganizationPatchSchema
from app.services.organization import OrganizationService

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

# Organization always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_organization",
    summary="Create a new Organization resource",
    description=(
        "Records a formally or informally recognized grouping of people or organizations "
        "formed for the purpose of achieving some form of collective action. "
        "The request body is a FHIR R4 Organization resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/organization.html); the organization and every supplied "
        "element (identifier, type, alias, telecom, address, contact, endpoint) are written "
        "atomically in one DB transaction. The body is checked against base FHIR R4: any valid "
        "R4 element is accepted and stored as sent (server-managed `id`/`meta` are ignored); "
        "a key that isn't FHIR at all is rejected with 422. Optionally link to a parent organization via `partOf` "
        '(e.g. `{"reference": "Organization/190001"}`) — rejected with 422 if the referenced '
        "organization doesn't exist. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_organization(
    payload: OrganizationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("organization", "create")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). Organization has no user_id
    field at all, unlike every other resource."""
    logger.info(
        "Create a new Organization resource",
        extra={"event": "route.create_organization"},
    )
    log_payload(logger, "organization.create.payload", payload)
    org = await organization_service.create_organization(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        organization_service._to_fhir(org), status_code=status.HTTP_201_CREATED
    )


@router.get(
    "/{organization_id}",
    operation_id="get_organization_by_id",
    summary="Retrieve an Organization resource by public organization_id",
    description=(
        "Scoped to the caller's own org — get_organization_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_organization(
    request: Request,
    organization_id: int = Path(
        ..., ge=1, description="Public organization identifier."
    ),
    actor: AuthUser = Depends(require_permission("organization", "read")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    logger.info(
        "Retrieve an Organization resource by public organization_id",
        extra={
            "event": "route.get_organization_by_id",
            "organization_id": organization_id,
        },
    )
    org = await organization_service.get_organization_scoped(
        organization_id, actor.org_id
    )
    return fhir_response(organization_service._to_fhir(org))


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{organization_id}",
    operation_id="patch_organization",
    summary="Update an Organization resource",
    description=(
        "The request body is a partial FHIR R4 Organization (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. Every supplied "
        "list (identifier, type, alias, telecom, address, contact, endpoint — even `[]`) "
        "atomically replaces the stored entries; a supplied `partOf` replaces the whole "
        "Reference, and `null` clears it — rejected with 422 if the referenced organization "
        "doesn't exist or setting it would create a circular hierarchy. "
        "Scoped to the caller's own org — patch_organization() raises NotFoundError (404, not "
        "403 — avoids leaking that an organization with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_organization(
    payload: OrganizationPatchSchema,
    request: Request,
    organization_id: int = Path(
        ..., ge=1, description="Public organization identifier."
    ),
    actor: AuthUser = Depends(require_permission("organization", "update")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_organization()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an Organization resource",
        extra={"event": "route.patch_organization", "organization_id": organization_id},
    )
    log_payload(logger, "organization.patch.payload", payload)
    updated = await organization_service.patch_organization(
        organization_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(organization_service._to_fhir(updated))


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains (`partof.name`) and repeat for AND, none
# of which fit FastAPI's per-name Query() declarations — and validated
# against the Organization search registry. The OpenAPI parameter list is
# generated from that same registry.

_SEARCH_REGISTRY = organization_search()
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
    organization_service: OrganizationService,
):
    search_url, fhir_base = search_urls(request, "search_organizations")
    search_request, rows, total, included = await organization_service.search_organizations(
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
    operation_id="search_organizations",
    summary="Search Organization resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_organizations(
    request: Request,
    actor: AuthUser = Depends(require_permission("organization", "read")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Organization resources",
        extra={"event": "route.search_organizations"},
    )
    return await _search(request, get_query(request), actor, organization_service)


@router.post(
    "/_search",
    operation_id="search_organizations_post",
    summary="Search Organization resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_organizations_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("organization", "read")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    logger.info(
        "Search Organization resources (POST _search)",
        extra={"event": "route.search_organizations_post"},
    )
    return await _search(request, await post_query(request), actor, organization_service)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_organization",
    summary="Delete an Organization resource",
    description=(
        "Permanently deletes the Organization and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "organization exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_organization(
    organization_id: int = Path(
        ..., ge=1, description="Public organization identifier."
    ),
    actor: AuthUser = Depends(require_permission("organization", "delete")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """delete_organization() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org. Delete
    cascades to every sub-resource row."""
    logger.info(
        "Delete an Organization resource",
        extra={
            "event": "route.delete_organization",
            "organization_id": organization_id,
        },
    )
    await organization_service.delete_organization(organization_id, org_id=actor.org_id)
