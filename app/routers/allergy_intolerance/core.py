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
from app.di.dependencies.allergy_intolerance import get_allergy_intolerance_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.allergy_intolerance.search import allergy_intolerance_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.allergy_intolerance import (
    AllergyIntoleranceCreateSchema,
    AllergyIntolerancePatchSchema,
)
from app.services.allergy_intolerance import AllergyIntoleranceService

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

# AllergyIntolerance always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_allergy_intolerance",
    summary="Create a new AllergyIntolerance resource",
    description=(
        "Records a harmful or undesirable physiological response associated with exposure to a substance — an "
        "allergy or intolerance of a patient. The request body is a FHIR R4 AllergyIntolerance resource "
        "(camelCase, nested datatypes — https://www.hl7.org/fhir/R4/allergyintolerance.html); every supplied "
        "element (identifier, clinicalStatus, verificationStatus, type, category, criticality, code, patient, "
        "encounter, onset[x], recordedDate, recorder, asserter, lastOccurrence, note, reaction) is stored as "
        "sent. R4 requires `patient`. The body is checked against base FHIR R4: any valid R4 element is accepted "
        "and stored as sent (server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected "
        "with 422. A relative `Patient/<id>`, `Encounter/<id>`, a recorder/asserter "
        "(Practitioner, PractitionerRole, Patient, RelatedPerson), a note author and `identifier.assigner` are "
        "rejected with 422 if they do not exist in the caller's org; an absolute URL or logical reference is "
        "stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_allergy_intolerance(
    payload: AllergyIntoleranceCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "create")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new AllergyIntolerance resource",
        extra={"event": "route.create_allergy_intolerance"},
    )
    log_payload(logger, "allergy_intolerance.create.payload", payload)
    allergy_intolerance = await allergy_intolerance_service.create_allergy_intolerance(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        allergy_intolerance_service._to_fhir(allergy_intolerance),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# AllergyIntolerance search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = allergy_intolerance_search()
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
    allergy_intolerance_service: AllergyIntoleranceService,
):
    search_url, fhir_base = search_urls(request, "search_allergy_intolerances")
    (
        search_request,
        rows,
        total,
        included,
    ) = await allergy_intolerance_service.search_allergy_intolerances(
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
    operation_id="search_allergy_intolerances",
    summary="Search AllergyIntolerance resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_allergy_intolerances(
    request: Request,
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "read")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search AllergyIntolerance resources",
        extra={"event": "route.search_allergy_intolerances"},
    )
    return await _search(
        request, get_query(request), actor, allergy_intolerance_service
    )


@router.post(
    "/_search",
    operation_id="search_allergy_intolerances_post",
    summary="Search AllergyIntolerance resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_allergy_intolerances_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "read")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    logger.info(
        "Search AllergyIntolerance resources (POST _search)",
        extra={"event": "route.search_allergy_intolerances_post"},
    )
    return await _search(
        request, await post_query(request), actor, allergy_intolerance_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{allergy_intolerance_id}",
    operation_id="get_allergy_intolerance_by_id",
    summary="Retrieve an AllergyIntolerance resource by public allergy_intolerance_id",
    description=(
        "Scoped to the caller's own org — get_allergy_intolerance_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_allergy_intolerance(
    request: Request,
    allergy_intolerance_id: int = Path(
        ..., ge=1, description="Public allergy_intolerance identifier."
    ),
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "read")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    logger.info(
        "Retrieve an AllergyIntolerance resource by public allergy_intolerance_id",
        extra={
            "event": "route.get_allergy_intolerance_by_id",
            "allergy_intolerance_id": allergy_intolerance_id,
        },
    )
    allergy_intolerance = (
        await allergy_intolerance_service.get_allergy_intolerance_scoped(
            allergy_intolerance_id, actor.org_id
        )
    )
    return fhir_response(allergy_intolerance_service._to_fhir(allergy_intolerance))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{allergy_intolerance_id}",
    operation_id="patch_allergy_intolerance",
    summary="Update an AllergyIntolerance resource",
    description=(
        "The request body is a partial FHIR R4 AllergyIntolerance (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, category, note, reaction — even `[]`) atomically replaces the stored entries, a "
        "supplied `patient`, `code` or `clinicalStatus` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_allergy_intolerance() raises NotFoundError (404, not "
        "403 — avoids leaking that an allergy or intolerance with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_allergy_intolerance(
    payload: AllergyIntolerancePatchSchema,
    request: Request,
    allergy_intolerance_id: int = Path(
        ..., ge=1, description="Public allergy_intolerance identifier."
    ),
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "update")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_allergy_intolerance()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an AllergyIntolerance resource",
        extra={
            "event": "route.patch_allergy_intolerance",
            "allergy_intolerance_id": allergy_intolerance_id,
        },
    )
    log_payload(logger, "allergy_intolerance.patch.payload", payload)
    updated = await allergy_intolerance_service.patch_allergy_intolerance(
        allergy_intolerance_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(allergy_intolerance_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{allergy_intolerance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_allergy_intolerance",
    summary="Delete an AllergyIntolerance resource",
    description=(
        "Permanently deletes the AllergyIntolerance and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "allergy_intolerance exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_allergy_intolerance(
    allergy_intolerance_id: int = Path(
        ..., ge=1, description="Public allergy_intolerance identifier."
    ),
    actor: AuthUser = Depends(require_permission("allergy_intolerance", "delete")),
    allergy_intolerance_service: AllergyIntoleranceService = Depends(
        get_allergy_intolerance_service
    ),
):
    """delete_allergy_intolerance() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an AllergyIntolerance resource",
        extra={
            "event": "route.delete_allergy_intolerance",
            "allergy_intolerance_id": allergy_intolerance_id,
        },
    )
    await allergy_intolerance_service.delete_allergy_intolerance(
        allergy_intolerance_id, org_id=actor.org_id
    )
