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
from app.di.dependencies.immunization import get_immunization_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.immunization.search import immunization_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.immunization import ImmunizationCreateSchema, ImmunizationPatchSchema
from app.services.immunization import ImmunizationService

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

# Immunization always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_immunization",
    summary="Create a new Immunization resource",
    description=(
        "Records the administration of a vaccine to a patient (or its non-administration / refusal). The "
        "request body is a FHIR R4 Immunization resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/immunization.html); every supplied element (identifier, status, statusReason, "
        "vaccineCode, patient, encounter, occurrence[x], recorded, primarySource, reportOrigin, location, "
        "manufacturer, lotNumber, expirationDate, site, route, doseQuantity, performer, note, reasonCode, "
        "reasonReference, isSubpotent, subpotentReason, education, programEligibility, fundingSource, reaction, "
        "protocolApplied) is stored as sent. R4 requires `status`, `vaccineCode`, `patient` and `occurrence[x]`. "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>`, `Encounter/<id>`, `Location/<id>`, `manufacturer`, a performer actor (Practitioner, "
        "PractitionerRole, Organization), a Condition or DiagnosticReport reason, `protocolApplied.authority` and "
        "`identifier.assigner` are rejected with 422 if they do not exist in the caller's org; an absolute URL, an "
        "Observation reason or reaction detail or a logical reference is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_immunization(
    payload: ImmunizationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization", "create")),
    immunization_service: ImmunizationService = Depends(get_immunization_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new Immunization resource",
        extra={"event": "route.create_immunization"},
    )
    log_payload(logger, "immunization.create.payload", payload)
    immunization = await immunization_service.create_immunization(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        immunization_service._to_fhir(immunization),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Immunization search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = immunization_search()
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
    immunization_service: ImmunizationService,
):
    search_url, fhir_base = search_urls(request, "search_immunizations")
    (
        search_request,
        rows,
        total,
        included,
    ) = await immunization_service.search_immunizations(
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
    operation_id="search_immunizations",
    summary="Search Immunization resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_immunizations(
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization", "read")),
    immunization_service: ImmunizationService = Depends(get_immunization_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Immunization resources",
        extra={"event": "route.search_immunizations"},
    )
    return await _search(request, get_query(request), actor, immunization_service)


@router.post(
    "/_search",
    operation_id="search_immunizations_post",
    summary="Search Immunization resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_immunizations_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("immunization", "read")),
    immunization_service: ImmunizationService = Depends(get_immunization_service),
):
    logger.info(
        "Search Immunization resources (POST _search)",
        extra={"event": "route.search_immunizations_post"},
    )
    return await _search(request, await post_query(request), actor, immunization_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{immunization_id}",
    operation_id="get_immunization_by_id",
    summary="Retrieve an Immunization resource by public immunization_id",
    description=(
        "Scoped to the caller's own org — get_immunization_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_immunization(
    request: Request,
    immunization_id: int = Path(
        ..., ge=1, description="Public immunization identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization", "read")),
    immunization_service: ImmunizationService = Depends(get_immunization_service),
):
    logger.info(
        "Retrieve an Immunization resource by public immunization_id",
        extra={
            "event": "route.get_immunization_by_id",
            "immunization_id": immunization_id,
        },
    )
    immunization = await immunization_service.get_immunization_scoped(
        immunization_id, actor.org_id
    )
    return fhir_response(immunization_service._to_fhir(immunization))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{immunization_id}",
    operation_id="patch_immunization",
    summary="Update an Immunization resource",
    description=(
        "The request body is a partial FHIR R4 Immunization (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, performer, note, reasonCode, reasonReference, reaction, protocolApplied — even `[]`) atomically replaces the stored entries, a "
        "supplied `patient`, `vaccineCode` or `doseQuantity` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_immunization() raises NotFoundError (404, not "
        "403 — avoids leaking that an immunization with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_immunization(
    payload: ImmunizationPatchSchema,
    request: Request,
    immunization_id: int = Path(
        ..., ge=1, description="Public immunization identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization", "update")),
    immunization_service: ImmunizationService = Depends(get_immunization_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_immunization()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an Immunization resource",
        extra={"event": "route.patch_immunization", "immunization_id": immunization_id},
    )
    log_payload(logger, "immunization.patch.payload", payload)
    updated = await immunization_service.patch_immunization(
        immunization_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(immunization_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{immunization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_immunization",
    summary="Delete an Immunization resource",
    description=(
        "Permanently deletes the Immunization and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "immunization exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_immunization(
    immunization_id: int = Path(
        ..., ge=1, description="Public immunization identifier."
    ),
    actor: AuthUser = Depends(require_permission("immunization", "delete")),
    immunization_service: ImmunizationService = Depends(get_immunization_service),
):
    """delete_immunization() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an Immunization resource",
        extra={
            "event": "route.delete_immunization",
            "immunization_id": immunization_id,
        },
    )
    await immunization_service.delete_immunization(immunization_id, org_id=actor.org_id)
