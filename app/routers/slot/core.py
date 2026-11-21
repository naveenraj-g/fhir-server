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
from app.di.dependencies.slot import get_slot_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.slot.search import slot_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.slot import SlotCreateSchema, SlotPatchSchema
from app.services.slot import SlotService

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

# Slot always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_slot",
    summary="Create a new Slot resource",
    description=(
        "Records a slot of time on a slot that may be available for booking appointments. "
        "The request body is a FHIR R4 Slot resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/slot.html); the slot and every supplied element (identifier, "
        "serviceCategory, serviceType, specialty, appointmentType, slot, status, start, end, "
        "overbooked, comment, ...) are written atomically in one DB transaction. R4 requires "
        "`slot`, `status`, `start` and `end`. The body is checked against base FHIR R4: any "
        "valid R4 element is accepted and stored as sent (server-managed `id`/`meta` are ignored); a "
        "key that isn't FHIR at all is rejected with 422. `slot` may reference a Slot "
        '(e.g. `{"reference": "Slot/200001"}`) — rejected with 422 if it doesn\'t exist in the '
        "caller's org. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_slot(
    payload: SlotCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("slot", "create")),
    slot_service: SlotService = Depends(get_slot_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new Slot resource",
        extra={"event": "route.create_slot"},
    )
    log_payload(logger, "slot.create.payload", payload)
    slot = await slot_service.create_slot(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        slot_service._to_fhir(slot),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Slot search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = slot_search()
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
    slot_service: SlotService,
):
    search_url, fhir_base = search_urls(request, "search_slots")
    (
        search_request,
        rows,
        total,
        included,
    ) = await slot_service.search_slots(
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
    operation_id="search_slots",
    summary="Search Slot resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_slots(
    request: Request,
    actor: AuthUser = Depends(require_permission("slot", "read")),
    slot_service: SlotService = Depends(get_slot_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Slot resources",
        extra={"event": "route.search_slots"},
    )
    return await _search(request, get_query(request), actor, slot_service)


@router.post(
    "/_search",
    operation_id="search_slots_post",
    summary="Search Slot resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_slots_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("slot", "read")),
    slot_service: SlotService = Depends(get_slot_service),
):
    logger.info(
        "Search Slot resources (POST _search)",
        extra={"event": "route.search_slots_post"},
    )
    return await _search(request, await post_query(request), actor, slot_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{slot_id}",
    operation_id="get_slot_by_id",
    summary="Retrieve a Slot resource by public slot_id",
    description=(
        "Scoped to the caller's own org — get_slot_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_slot(
    request: Request,
    slot_id: int = Path(..., ge=1, description="Public slot identifier."),
    actor: AuthUser = Depends(require_permission("slot", "read")),
    slot_service: SlotService = Depends(get_slot_service),
):
    logger.info(
        "Retrieve a Slot resource by public slot_id",
        extra={
            "event": "route.get_slot_by_id",
            "slot_id": slot_id,
        },
    )
    slot = await slot_service.get_slot_scoped(slot_id, actor.org_id)
    return fhir_response(slot_service._to_fhir(slot))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{slot_id}",
    operation_id="patch_slot",
    summary="Update a Slot resource",
    description=(
        "The request body is a partial FHIR R4 Slot (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. Every supplied "
        "list (identifier, serviceCategory, serviceType, specialty — even `[]`) atomically replaces "
        "the stored entries, a supplied `slot` or `appointmentType` replaces the whole value, and "
        "`null` clears an element. "
        "Scoped to the caller's own org — patch_slot() raises NotFoundError (404, not "
        "403 — avoids leaking that a slot with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_slot(
    payload: SlotPatchSchema,
    request: Request,
    slot_id: int = Path(..., ge=1, description="Public slot identifier."),
    actor: AuthUser = Depends(require_permission("slot", "update")),
    slot_service: SlotService = Depends(get_slot_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_slot()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Slot resource",
        extra={"event": "route.patch_slot", "slot_id": slot_id},
    )
    log_payload(logger, "slot.patch.payload", payload)
    updated = await slot_service.patch_slot(
        slot_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(slot_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_slot",
    summary="Delete a Slot resource",
    description=(
        "Permanently deletes the Slot and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "slot exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_slot(
    slot_id: int = Path(..., ge=1, description="Public slot identifier."),
    actor: AuthUser = Depends(require_permission("slot", "delete")),
    slot_service: SlotService = Depends(get_slot_service),
):
    """delete_slot() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a Slot resource",
        extra={
            "event": "route.delete_slot",
            "slot_id": slot_id,
        },
    )
    await slot_service.delete_slot(slot_id, org_id=actor.org_id)
