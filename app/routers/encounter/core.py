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
from app.di.dependencies.encounter import get_encounter_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.encounter.search import encounter_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema
from app.services.encounter import EncounterService

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

# Encounter always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_encounter",
    summary="Create a new Encounter resource",
    description=(
        "Records an interaction between a patient and healthcare provider(s) — a visit, admission or "
        "other contact. The request body is a FHIR R4 Encounter resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/encounter.html); every supplied element (identifier, status, "
        "statusHistory, class, classHistory, type, serviceType, priority, subject, episodeOfCare, basedOn, "
        "participant, appointment, period, length, reasonCode, reasonReference, diagnosis, account, "
        "hospitalization, location, serviceProvider, partOf) is stored as sent. R4 requires `status` and "
        "`class`. The body is checked against base FHIR R4: any valid R4 element is accepted and stored as "
        "sent (server-managed `id`/`meta` are ignored); a key that isn't FHIR at all is rejected with 422. "
        "A relative reference to a Patient `subject`, `partOf` (Encounter), `serviceProvider` (Organization), "
        "`appointment`, a Practitioner/PractitionerRole participant individual, a `location.location`, "
        "`hospitalization.origin`/`destination` or `identifier.assigner` is rejected with 422 if it doesn't "
        "exist in the caller's org; other references (Group, RelatedPerson, Account, EpisodeOfCare, "
        "ServiceRequest, Condition, ...) are stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_encounter(
    payload: EncounterCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("encounter", "create")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new Encounter resource",
        extra={"event": "route.create_encounter"},
    )
    log_payload(logger, "encounter.create.payload", payload)
    encounter = await encounter_service.create_encounter(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        encounter_service._to_fhir(encounter),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Encounter search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = encounter_search()
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
    encounter_service: EncounterService,
):
    search_url, fhir_base = search_urls(request, "search_encounters")
    (
        search_request,
        rows,
        total,
        included,
    ) = await encounter_service.search_encounters(
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
    operation_id="search_encounters",
    summary="Search Encounter resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_encounters(
    request: Request,
    actor: AuthUser = Depends(require_permission("encounter", "read")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Encounter resources",
        extra={"event": "route.search_encounters"},
    )
    return await _search(request, get_query(request), actor, encounter_service)


@router.post(
    "/_search",
    operation_id="search_encounters_post",
    summary="Search Encounter resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_encounters_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("encounter", "read")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    logger.info(
        "Search Encounter resources (POST _search)",
        extra={"event": "route.search_encounters_post"},
    )
    return await _search(request, await post_query(request), actor, encounter_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{encounter_id}",
    operation_id="get_encounter_by_id",
    summary="Retrieve an Encounter resource by public encounter_id",
    description=(
        "Scoped to the caller's own org — get_encounter_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_encounter(
    request: Request,
    encounter_id: int = Path(..., ge=1, description="Public encounter identifier."),
    actor: AuthUser = Depends(require_permission("encounter", "read")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    logger.info(
        "Retrieve an Encounter resource by public encounter_id",
        extra={
            "event": "route.get_encounter_by_id",
            "encounter_id": encounter_id,
        },
    )
    encounter = await encounter_service.get_encounter_scoped(encounter_id, actor.org_id)
    return fhir_response(encounter_service._to_fhir(encounter))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{encounter_id}",
    operation_id="patch_encounter",
    summary="Update an Encounter resource",
    description=(
        "The request body is a partial FHIR R4 Encounter (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, type, participant, location, diagnosis — even `[]`) atomically replaces the stored entries, a "
        "supplied `class`, `period`, `subject` or `hospitalization` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_encounter() raises NotFoundError (404, not "
        "403 — avoids leaking that an encounter with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_encounter(
    payload: EncounterPatchSchema,
    request: Request,
    encounter_id: int = Path(..., ge=1, description="Public encounter identifier."),
    actor: AuthUser = Depends(require_permission("encounter", "update")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_encounter()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an Encounter resource",
        extra={"event": "route.patch_encounter", "encounter_id": encounter_id},
    )
    log_payload(logger, "encounter.patch.payload", payload)
    updated = await encounter_service.patch_encounter(
        encounter_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(encounter_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{encounter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_encounter",
    summary="Delete an Encounter resource",
    description=(
        "Permanently deletes the Encounter and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "encounter exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_encounter(
    encounter_id: int = Path(..., ge=1, description="Public encounter identifier."),
    actor: AuthUser = Depends(require_permission("encounter", "delete")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    """delete_encounter() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an Encounter resource",
        extra={
            "event": "route.delete_encounter",
            "encounter_id": encounter_id,
        },
    )
    await encounter_service.delete_encounter(encounter_id, org_id=actor.org_id)
