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
from app.di.dependencies.observation import get_observation_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.observation.search import observation_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.observation import ObservationCreateSchema, ObservationPatchSchema
from app.services.observation import ObservationService

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

# Observation always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_observation",
    summary="Create a new Observation resource",
    description=(
        "Records a measurement or simple assertion made about a patient, device or other subject — a vital "
        "sign, a lab result, a social-history item. The request body is a FHIR R4 Observation resource "
        "(camelCase, nested datatypes — https://www.hl7.org/fhir/R4/observation.html); every supplied "
        "element (identifier, basedOn, partOf, status, category, code, subject, focus, encounter, effective[x], "
        "issued, performer, value[x], dataAbsentReason, interpretation, note, bodySite, method, specimen, device, "
        "referenceRange, hasMember, derivedFrom, component) is stored as sent. R4 requires `status` and `code`. "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient`, `Group` or `Location` subject, `Encounter/<id>`, `Specimen/<id>`, and every basedOn, partOf, "
        "performer, hasMember, derivedFrom and note author that is a resource this server holds, and "
        "`identifier.assigner`, are rejected with 422 if they do not exist in the caller's org; a Device subject "
        "or device, `focus` (Reference(Any)), an ImagingStudy / Media / MolecularSequence target, an absolute URL "
        "or a logical reference is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_observation(
    payload: ObservationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("observation", "create")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new Observation resource",
        extra={"event": "route.create_observation"},
    )
    log_payload(logger, "observation.create.payload", payload)
    observation = await observation_service.create_observation(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        observation_service._to_fhir(observation),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Observation search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = observation_search()
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
    observation_service: ObservationService,
):
    search_url, fhir_base = search_urls(request, "search_observations")
    (
        search_request,
        rows,
        total,
        included,
    ) = await observation_service.search_observations(
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
    operation_id="search_observations",
    summary="Search Observation resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_observations(
    request: Request,
    actor: AuthUser = Depends(require_permission("observation", "read")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Observation resources",
        extra={"event": "route.search_observations"},
    )
    return await _search(request, get_query(request), actor, observation_service)


@router.post(
    "/_search",
    operation_id="search_observations_post",
    summary="Search Observation resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_observations_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("observation", "read")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info(
        "Search Observation resources (POST _search)",
        extra={"event": "route.search_observations_post"},
    )
    return await _search(request, await post_query(request), actor, observation_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{observation_id}",
    operation_id="get_observation_by_id",
    summary="Retrieve an Observation resource by public observation_id",
    description=(
        "Scoped to the caller's own org — get_observation_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_observation(
    request: Request,
    observation_id: int = Path(
        ..., ge=1, description="Public observation identifier."
    ),
    actor: AuthUser = Depends(require_permission("observation", "read")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    logger.info(
        "Retrieve an Observation resource by public observation_id",
        extra={
            "event": "route.get_observation_by_id",
            "observation_id": observation_id,
        },
    )
    observation = await observation_service.get_observation_scoped(
        observation_id, actor.org_id
    )
    return fhir_response(observation_service._to_fhir(observation))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{observation_id}",
    operation_id="patch_observation",
    summary="Update a Observation resource",
    description=(
        "The request body is a partial FHIR R4 Observation (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, category, performer, component, referenceRange, note — even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `code` or `valueQuantity` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_observation() raises NotFoundError (404, not "
        "403 — avoids leaking that a Observation with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_observation(
    payload: ObservationPatchSchema,
    request: Request,
    observation_id: int = Path(
        ..., ge=1, description="Public observation identifier."
    ),
    actor: AuthUser = Depends(require_permission("observation", "update")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_observation()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Observation resource",
        extra={"event": "route.patch_observation", "observation_id": observation_id},
    )
    log_payload(logger, "observation.patch.payload", payload)
    updated = await observation_service.patch_observation(
        observation_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(observation_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_observation",
    summary="Delete an Observation resource",
    description=(
        "Permanently deletes the Observation and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "observation exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_observation(
    observation_id: int = Path(
        ..., ge=1, description="Public observation identifier."
    ),
    actor: AuthUser = Depends(require_permission("observation", "delete")),
    observation_service: ObservationService = Depends(get_observation_service),
):
    """delete_observation() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an Observation resource",
        extra={
            "event": "route.delete_observation",
            "observation_id": observation_id,
        },
    )
    await observation_service.delete_observation(observation_id, org_id=actor.org_id)
