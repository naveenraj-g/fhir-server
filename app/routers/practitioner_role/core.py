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
from app.di.dependencies.practitioner_role import get_practitioner_role_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.practitioner_role.search import practitioner_role_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.practitioner_role import (
    PractitionerRoleCreateSchema,
    PractitionerRolePatchSchema,
)
from app.services.practitioner_role import PractitionerRoleService

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

# PractitionerRole always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_practitioner_role",
    summary="Create a new PractitionerRole resource",
    description=(
        "Records the roles, specialties, locations and services a practitioner provides for an "
        "organization. The request body is a FHIR R4 PractitionerRole resource (camelCase, nested "
        "datatypes — https://www.hl7.org/fhir/R4/practitionerrole.html); the role and every supplied "
        "element (identifier, period, code, specialty, location, healthcareService, telecom, "
        "availableTime, notAvailable, endpoint, ...) are written atomically in one DB transaction. "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as "
        "sent (server-managed `id`/`meta` are ignored); a key that isn't FHIR at all is rejected with "
        "422. `practitioner` may reference a Practitioner, `organization` an Organization, `location` "
        "a Location, `healthcareService` a PractitionerRole and `endpoint` an Endpoint "
        '(e.g. `{"reference": "Practitioner/30001"}`) — rejected with 422 if the referenced resource '
        "doesn't exist in the caller's org. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_practitioner_role(
    payload: PractitionerRoleCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner_role", "create")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new PractitionerRole resource",
        extra={"event": "route.create_practitioner_role"},
    )
    log_payload(logger, "practitioner_role.create.payload", payload)
    practitioner_role = await practitioner_role_service.create_practitioner_role(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        practitioner_role_service._to_fhir(practitioner_role),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# PractitionerRole search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = practitioner_role_search()
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
    practitioner_role_service: PractitionerRoleService,
):
    search_url, fhir_base = search_urls(request, "search_practitioner_roles")
    (
        search_request,
        rows,
        total,
        included,
    ) = await practitioner_role_service.search_practitioner_roles(
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
    operation_id="search_practitioner_roles",
    summary="Search PractitionerRole resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_practitioner_roles(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner_role", "read")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search PractitionerRole resources",
        extra={"event": "route.search_practitioner_roles"},
    )
    return await _search(request, get_query(request), actor, practitioner_role_service)


@router.post(
    "/_search",
    operation_id="search_practitioner_roles_post",
    summary="Search PractitionerRole resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_practitioner_roles_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner_role", "read")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    logger.info(
        "Search PractitionerRole resources (POST _search)",
        extra={"event": "route.search_practitioner_roles_post"},
    )
    return await _search(
        request, await post_query(request), actor, practitioner_role_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{practitioner_role_id}",
    operation_id="get_practitioner_role_by_id",
    summary="Retrieve a PractitionerRole resource by public practitioner_role_id",
    description=(
        "Scoped to the caller's own org — get_practitioner_role_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_practitioner_role(
    request: Request,
    practitioner_role_id: int = Path(
        ..., ge=1, description="Public practitioner_role identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner_role", "read")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    logger.info(
        "Retrieve a PractitionerRole resource by public practitioner_role_id",
        extra={
            "event": "route.get_practitioner_role_by_id",
            "practitioner_role_id": practitioner_role_id,
        },
    )
    practitioner_role = await practitioner_role_service.get_practitioner_role_scoped(
        practitioner_role_id, actor.org_id
    )
    return fhir_response(practitioner_role_service._to_fhir(practitioner_role))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{practitioner_role_id}",
    operation_id="patch_practitioner_role",
    summary="Update a PractitionerRole resource",
    description=(
        "The request body is a partial FHIR R4 PractitionerRole (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. Every supplied "
        "list (identifier, code, specialty, location, healthcareService, telecom, availableTime, "
        "notAvailable, endpoint — even `[]`) atomically replaces the stored entries, a supplied "
        "`practitioner`, `organization` or `period` replaces the whole value, and `null` clears an "
        "element. "
        "Scoped to the caller's own org — patch_practitioner_role() raises NotFoundError (404, not "
        "403 — avoids leaking that a practitioner_role with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner_role(
    payload: PractitionerRolePatchSchema,
    request: Request,
    practitioner_role_id: int = Path(
        ..., ge=1, description="Public practitioner_role identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner_role", "update")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_practitioner_role()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a PractitionerRole resource",
        extra={
            "event": "route.patch_practitioner_role",
            "practitioner_role_id": practitioner_role_id,
        },
    )
    log_payload(logger, "practitioner_role.patch.payload", payload)
    updated = await practitioner_role_service.patch_practitioner_role(
        practitioner_role_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(practitioner_role_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{practitioner_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_role",
    summary="Delete a PractitionerRole resource",
    description=(
        "Permanently deletes the PractitionerRole and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "practitioner_role exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_practitioner_role(
    practitioner_role_id: int = Path(
        ..., ge=1, description="Public practitioner_role identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner_role", "delete")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    """delete_practitioner_role() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a PractitionerRole resource",
        extra={
            "event": "route.delete_practitioner_role",
            "practitioner_role_id": practitioner_role_id,
        },
    )
    await practitioner_role_service.delete_practitioner_role(
        practitioner_role_id, org_id=actor.org_id
    )
