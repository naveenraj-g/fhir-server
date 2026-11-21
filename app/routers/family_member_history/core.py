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
from app.di.dependencies.family_member_history import get_family_member_history_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.family_member_history.search import family_member_history_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.family_member_history import FamilyMemberHistoryCreateSchema, FamilyMemberHistoryPatchSchema
from app.services.family_member_history import FamilyMemberHistoryService

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

# FamilyMemberHistory always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_family_member_history",
    summary="Create a new FamilyMemberHistory resource",
    description=(
        "Records significant health conditions of a person related to the patient (a parent, sibling, ...), "
        "relevant to the patient's own health. The request body is a FHIR R4 FamilyMemberHistory resource "
        "(camelCase, nested datatypes — https://www.hl7.org/fhir/R4/familymemberhistory.html); every supplied "
        "element (identifier, instantiatesCanonical, instantiatesUri, status, dataAbsentReason, patient, date, "
        "name, relationship, sex, born[x], age[x], estimatedAge, deceased[x], reasonCode, reasonReference, note, "
        "condition) is stored as sent. R4 requires `status`, `patient` and `relationship`, and rules fhs-1 "
        "(`age[x]` or `born[x]`, not both) and fhs-2 (`estimatedAge` needs `age[x]`). "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>`, a Condition, AllergyIntolerance or DiagnosticReport reason, a note author "
        "(Practitioner, PractitionerRole, Patient, RelatedPerson, Organization) and `identifier.assigner` are "
        "rejected with 422 if they do not exist in the caller's org; an Observation / QuestionnaireResponse / "
        "DocumentReference reason, an absolute URL or a logical reference is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_family_member_history(
    payload: FamilyMemberHistoryCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("family_member_history", "create")),
    family_member_history_service: FamilyMemberHistoryService = Depends(get_family_member_history_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new FamilyMemberHistory resource",
        extra={"event": "route.create_family_member_history"},
    )
    log_payload(logger, "family_member_history.create.payload", payload)
    family_member_history = await family_member_history_service.create_family_member_history(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        family_member_history_service._to_fhir(family_member_history),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# FamilyMemberHistory search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = family_member_history_search()
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
    family_member_history_service: FamilyMemberHistoryService,
):
    search_url, fhir_base = search_urls(request, "search_family_member_histories")
    (
        search_request,
        rows,
        total,
        included,
    ) = await family_member_history_service.search_family_member_histories(
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
    operation_id="search_family_member_histories",
    summary="Search FamilyMemberHistory resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_family_member_histories(
    request: Request,
    actor: AuthUser = Depends(require_permission("family_member_history", "read")),
    family_member_history_service: FamilyMemberHistoryService = Depends(get_family_member_history_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search FamilyMemberHistory resources",
        extra={"event": "route.search_family_member_histories"},
    )
    return await _search(request, get_query(request), actor, family_member_history_service)


@router.post(
    "/_search",
    operation_id="search_family_member_histories_post",
    summary="Search FamilyMemberHistory resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_family_member_histories_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("family_member_history", "read")),
    family_member_history_service: FamilyMemberHistoryService = Depends(get_family_member_history_service),
):
    logger.info(
        "Search FamilyMemberHistory resources (POST _search)",
        extra={"event": "route.search_family_member_histories_post"},
    )
    return await _search(request, await post_query(request), actor, family_member_history_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{family_member_history_id}",
    operation_id="get_family_member_history_by_id",
    summary="Retrieve an FamilyMemberHistory resource by public family_member_history_id",
    description=(
        "Scoped to the caller's own org — get_family_member_history_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_family_member_history(
    request: Request,
    family_member_history_id: int = Path(
        ..., ge=1, description="Public family_member_history identifier."
    ),
    actor: AuthUser = Depends(require_permission("family_member_history", "read")),
    family_member_history_service: FamilyMemberHistoryService = Depends(get_family_member_history_service),
):
    logger.info(
        "Retrieve an FamilyMemberHistory resource by public family_member_history_id",
        extra={
            "event": "route.get_family_member_history_by_id",
            "family_member_history_id": family_member_history_id,
        },
    )
    family_member_history = await family_member_history_service.get_family_member_history_scoped(
        family_member_history_id, actor.org_id
    )
    return fhir_response(family_member_history_service._to_fhir(family_member_history))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{family_member_history_id}",
    operation_id="patch_family_member_history",
    summary="Update an FamilyMemberHistory resource",
    description=(
        "The request body is a partial FHIR R4 FamilyMemberHistory (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, instantiatesCanonical, reasonCode, reasonReference, note, condition — even `[]`) atomically replaces the stored entries, a "
        "supplied `patient`, `relationship` or `sex` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_family_member_history() raises NotFoundError (404, not "
        "403 — avoids leaking that a FamilyMemberHistory with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_family_member_history(
    payload: FamilyMemberHistoryPatchSchema,
    request: Request,
    family_member_history_id: int = Path(
        ..., ge=1, description="Public family_member_history identifier."
    ),
    actor: AuthUser = Depends(require_permission("family_member_history", "update")),
    family_member_history_service: FamilyMemberHistoryService = Depends(get_family_member_history_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_family_member_history()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an FamilyMemberHistory resource",
        extra={"event": "route.patch_family_member_history", "family_member_history_id": family_member_history_id},
    )
    log_payload(logger, "family_member_history.patch.payload", payload)
    updated = await family_member_history_service.patch_family_member_history(
        family_member_history_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(family_member_history_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{family_member_history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_family_member_history",
    summary="Delete an FamilyMemberHistory resource",
    description=(
        "Permanently deletes the FamilyMemberHistory and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "family_member_history exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_family_member_history(
    family_member_history_id: int = Path(
        ..., ge=1, description="Public family_member_history identifier."
    ),
    actor: AuthUser = Depends(require_permission("family_member_history", "delete")),
    family_member_history_service: FamilyMemberHistoryService = Depends(get_family_member_history_service),
):
    """delete_family_member_history() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an FamilyMemberHistory resource",
        extra={
            "event": "route.delete_family_member_history",
            "family_member_history_id": family_member_history_id,
        },
    )
    await family_member_history_service.delete_family_member_history(family_member_history_id, org_id=actor.org_id)
