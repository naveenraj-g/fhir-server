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
from app.di.dependencies.episode_of_care import get_episode_of_care_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.episode_of_care.search import episode_of_care_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.episode_of_care import (
    EpisodeOfCareCreateSchema,
    EpisodeOfCarePatchSchema,
)
from app.services.episode_of_care import EpisodeOfCareService

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

# EpisodeOfCare always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_episode_of_care",
    summary="Create a new EpisodeOfCare resource",
    description=(
        "Records an association between a patient and an organization / healthcare provider(s) during "
        "which encounters and healthcare services may occur. The request body is a FHIR R4 EpisodeOfCare "
        "resource (camelCase, nested datatypes — https://www.hl7.org/fhir/R4/episodeofcare.html); every "
        "supplied element (identifier, status, statusHistory, type, diagnosis, patient, managingOrganization, "
        "period, referralRequest, careManager, team, account) is stored as sent. R4 requires `status` and "
        "`patient`, which only the java_validator backend enforces. The body is checked against base FHIR R4: "
        "any valid R4 element is accepted and stored as sent (server-managed `id`/`meta` are ignored); a key "
        "that is not FHIR at all is rejected with 422. A relative `Patient/<id>` patient, `managingOrganization`, "
        "`careManager` (Practitioner or PractitionerRole), every `referralRequest` (ServiceRequest), `team` "
        "(CareTeam), `diagnosis.condition` (Condition) and every identifier's `assigner` are rejected with 422 "
        "if they do not exist in the caller's org; an Account, an absolute URL or a logical reference is stored as sent. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_episode_of_care(
    payload: EpisodeOfCareCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("episode_of_care", "create")),
    episode_of_care_service: EpisodeOfCareService = Depends(
        get_episode_of_care_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new EpisodeOfCare resource",
        extra={"event": "route.create_episode_of_care"},
    )
    log_payload(logger, "episode_of_care.create.payload", payload)
    episode_of_care = await episode_of_care_service.create_episode_of_care(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        episode_of_care_service._to_fhir(episode_of_care),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# EpisodeOfCare search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = episode_of_care_search()
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
    episode_of_care_service: EpisodeOfCareService,
):
    search_url, fhir_base = search_urls(request, "search_episode_of_cares")
    (
        search_request,
        rows,
        total,
        included,
    ) = await episode_of_care_service.search_episode_of_cares(
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
    operation_id="search_episode_of_cares",
    summary="Search EpisodeOfCare resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_episode_of_cares(
    request: Request,
    actor: AuthUser = Depends(require_permission("episode_of_care", "read")),
    episode_of_care_service: EpisodeOfCareService = Depends(
        get_episode_of_care_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search EpisodeOfCare resources",
        extra={"event": "route.search_episode_of_cares"},
    )
    return await _search(request, get_query(request), actor, episode_of_care_service)


@router.post(
    "/_search",
    operation_id="search_episode_of_cares_post",
    summary="Search EpisodeOfCare resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_episode_of_cares_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("episode_of_care", "read")),
    episode_of_care_service: EpisodeOfCareService = Depends(
        get_episode_of_care_service
    ),
):
    logger.info(
        "Search EpisodeOfCare resources (POST _search)",
        extra={"event": "route.search_episode_of_cares_post"},
    )
    return await _search(
        request, await post_query(request), actor, episode_of_care_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{episode_of_care_id}",
    operation_id="get_episode_of_care_by_id",
    summary="Retrieve an EpisodeOfCare resource by public episode_of_care_id",
    description=(
        "Scoped to the caller's own org — get_episode_of_care_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_episode_of_care(
    request: Request,
    episode_of_care_id: int = Path(
        ..., ge=1, description="Public episode_of_care identifier."
    ),
    actor: AuthUser = Depends(require_permission("episode_of_care", "read")),
    episode_of_care_service: EpisodeOfCareService = Depends(
        get_episode_of_care_service
    ),
):
    logger.info(
        "Retrieve an EpisodeOfCare resource by public episode_of_care_id",
        extra={
            "event": "route.get_episode_of_care_by_id",
            "episode_of_care_id": episode_of_care_id,
        },
    )
    episode_of_care = await episode_of_care_service.get_episode_of_care_scoped(
        episode_of_care_id, actor.org_id
    )
    return fhir_response(episode_of_care_service._to_fhir(episode_of_care))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{episode_of_care_id}",
    operation_id="patch_episode_of_care",
    summary="Update an EpisodeOfCare resource",
    description=(
        "The request body is a partial FHIR R4 EpisodeOfCare (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, statusHistory, type, diagnosis, referralRequest, team, account — even `[]`) atomically replaces the stored entries, a "
        "supplied `patient`, `managingOrganization`, `careManager` or `period` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_episode_of_care() raises NotFoundError (404, not "
        "403 — avoids leaking that an EpisodeOfCare with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_episode_of_care(
    payload: EpisodeOfCarePatchSchema,
    request: Request,
    episode_of_care_id: int = Path(
        ..., ge=1, description="Public episode_of_care identifier."
    ),
    actor: AuthUser = Depends(require_permission("episode_of_care", "update")),
    episode_of_care_service: EpisodeOfCareService = Depends(
        get_episode_of_care_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_episode_of_care()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an EpisodeOfCare resource",
        extra={
            "event": "route.patch_episode_of_care",
            "episode_of_care_id": episode_of_care_id,
        },
    )
    log_payload(logger, "episode_of_care.patch.payload", payload)
    updated = await episode_of_care_service.patch_episode_of_care(
        episode_of_care_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(episode_of_care_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{episode_of_care_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_episode_of_care",
    summary="Delete an EpisodeOfCare resource",
    description=(
        "Permanently deletes the EpisodeOfCare and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "episode_of_care exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_episode_of_care(
    episode_of_care_id: int = Path(
        ..., ge=1, description="Public episode_of_care identifier."
    ),
    actor: AuthUser = Depends(require_permission("episode_of_care", "delete")),
    episode_of_care_service: EpisodeOfCareService = Depends(
        get_episode_of_care_service
    ),
):
    """delete_episode_of_care() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an EpisodeOfCare resource",
        extra={
            "event": "route.delete_episode_of_care",
            "episode_of_care_id": episode_of_care_id,
        },
    )
    await episode_of_care_service.delete_episode_of_care(
        episode_of_care_id, org_id=actor.org_id
    )
