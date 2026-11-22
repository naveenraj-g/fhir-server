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
from app.di.dependencies.care_plan import get_care_plan_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.care_plan.search import care_plan_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.care_plan import (
    CarePlanCreateSchema,
    CarePlanPatchSchema,
)
from app.services.care_plan import CarePlanService

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

# CarePlan always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_care_plan",
    summary="Create a new CarePlan resource",
    description=(
        "Records a plan of care for a patient or a group - its intent, category, period, the care teams, "
        "conditions and goals it addresses, and the activities (each a reference to an order or a detail "
        "with its schedule, performers and product). The request body is a FHIR R4 CarePlan resource "
        "(camelCase, nested datatypes - https://www.hl7.org/fhir/R4/careplan.html); every supplied element "
        "(identifier, instantiatesCanonical, instantiatesUri, basedOn, replaces, partOf, status, intent, "
        "category, title, description, subject, encounter, period, created, author, contributor, careTeam, "
        "addresses, supportingInfo, goal, activity, note) is stored as sent. R4 requires `status`, `intent` "
        "and `subject`. The body is checked against base FHIR R4: any valid R4 element is accepted and stored "
        "as sent (server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. "
        "A relative `Patient/<id>` or `Group/<id>` subject, `encounter`, `basedOn` / `replaces` / `partOf` "
        "(CarePlan), `author` / `contributor`, `careTeam`, `addresses` (Condition), `supportingInfo`, every "
        "`activity.reference` (Appointment, MedicationRequest, ServiceRequest) and activity detail "
        "`performer` / `location` / `reasonReference` / `productReference`, a note author and every "
        "identifier's `assigner` are rejected with 422 if they do not exist in the caller's org; a Goal, "
        "Device or a resource not built here, an absolute URL or a logical reference is stored as sent. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_care_plan(
    payload: CarePlanCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_plan", "create")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new CarePlan resource",
        extra={"event": "route.create_care_plan"},
    )
    log_payload(logger, "care_plan.create.payload", payload)
    care_plan = await care_plan_service.create_care_plan(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        care_plan_service._to_fhir(care_plan),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# CarePlan search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = care_plan_search()
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
    care_plan_service: CarePlanService,
):
    search_url, fhir_base = search_urls(request, "search_care_plans")
    (
        search_request,
        rows,
        total,
        included,
    ) = await care_plan_service.search_care_plans(
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
    operation_id="search_care_plans",
    summary="Search CarePlan resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_care_plans(
    request: Request,
    actor: AuthUser = Depends(require_permission("care_plan", "read")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search CarePlan resources",
        extra={"event": "route.search_care_plans"},
    )
    return await _search(request, get_query(request), actor, care_plan_service)


@router.post(
    "/_search",
    operation_id="search_care_plans_post",
    summary="Search CarePlan resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_care_plans_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("care_plan", "read")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    logger.info(
        "Search CarePlan resources (POST _search)",
        extra={"event": "route.search_care_plans_post"},
    )
    return await _search(request, await post_query(request), actor, care_plan_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{care_plan_id}",
    operation_id="get_care_plan_by_id",
    summary="Retrieve a CarePlan resource by public care_plan_id",
    description=(
        "Scoped to the caller's own org — get_care_plan_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_care_plan(
    request: Request,
    care_plan_id: int = Path(..., ge=1, description="Public care_plan identifier."),
    actor: AuthUser = Depends(require_permission("care_plan", "read")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    logger.info(
        "Retrieve a CarePlan resource by public care_plan_id",
        extra={
            "event": "route.get_care_plan_by_id",
            "care_plan_id": care_plan_id,
        },
    )
    care_plan = await care_plan_service.get_care_plan_scoped(care_plan_id, actor.org_id)
    return fhir_response(care_plan_service._to_fhir(care_plan))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{care_plan_id}",
    operation_id="patch_care_plan",
    summary="Update a CarePlan resource",
    description=(
        "The request body is a partial FHIR R4 CarePlan (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, category, basedOn, replaces, partOf, contributor, careTeam, addresses, supportingInfo, goal, activity, note — even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `encounter`, `period` or `author` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_care_plan() raises NotFoundError (404, not "
        "403 — avoids leaking that a CarePlan with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_care_plan(
    payload: CarePlanPatchSchema,
    request: Request,
    care_plan_id: int = Path(..., ge=1, description="Public care_plan identifier."),
    actor: AuthUser = Depends(require_permission("care_plan", "update")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_care_plan()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a CarePlan resource",
        extra={
            "event": "route.patch_care_plan",
            "care_plan_id": care_plan_id,
        },
    )
    log_payload(logger, "care_plan.patch.payload", payload)
    updated = await care_plan_service.patch_care_plan(
        care_plan_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(care_plan_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{care_plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_care_plan",
    summary="Delete a CarePlan resource",
    description=(
        "Permanently deletes the CarePlan and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "care_plan exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_care_plan(
    care_plan_id: int = Path(..., ge=1, description="Public care_plan identifier."),
    actor: AuthUser = Depends(require_permission("care_plan", "delete")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    """delete_care_plan() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a CarePlan resource",
        extra={
            "event": "route.delete_care_plan",
            "care_plan_id": care_plan_id,
        },
    )
    await care_plan_service.delete_care_plan(care_plan_id, org_id=actor.org_id)
