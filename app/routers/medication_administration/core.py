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
from app.di.dependencies.medication_administration import (
    get_medication_administration_service,
)
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.medication_administration.search import (
    medication_administration_search,
)
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.medication_administration import (
    MedicationAdministrationCreateSchema,
    MedicationAdministrationPatchSchema,
)
from app.services.medication_administration import MedicationAdministrationService

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

# MedicationAdministration always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_medication_administration",
    summary="Create a new MedicationAdministration resource",
    description=(
        "Records the administration of a medication to a patient or a group - an event that is in progress, "
        "completed or not done. The request body is a FHIR R4 MedicationAdministration resource (camelCase, "
        "nested datatypes - https://www.hl7.org/fhir/R4/medicationadministration.html); every supplied element "
        "(identifier, instantiates, partOf, status, statusReason, category, medication[x], subject, context, "
        "supportingInformation, effective[x], performer, reasonCode, reasonReference, request, device, note, "
        "dosage, eventHistory) is stored as sent. R4 requires `status`, `medication[x]`, `subject` and "
        "`effective[x]`, which only the java_validator backend enforces. The body is checked against base FHIR "
        "R4: any valid R4 element is accepted and stored as sent (server-managed `id`/`meta` are ignored); a key "
        "that is not FHIR at all is rejected with 422. A relative reference to a resource this server has - "
        "`subject`, `context`, `medicationReference`, `request`, `performer.actor`, `partOf`, "
        "`supportingInformation`, `reasonReference`, a note author and every identifier's `assigner` - is "
        "rejected with 422 if it does not exist in the caller's org; an absolute URL, a logical reference or a "
        "resource type this server does not have is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_medication_administration(
    payload: MedicationAdministrationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(
        require_permission("medication_administration", "create")
    ),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new MedicationAdministration resource",
        extra={"event": "route.create_medication_administration"},
    )
    log_payload(logger, "medication_administration.create.payload", payload)
    medication_administration = (
        await medication_administration_service.create_medication_administration(
            payload, actor.org_id, actor.sub, body=await request.json()
        )
    )
    return fhir_response(
        medication_administration_service._to_fhir(medication_administration),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# MedicationAdministration search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = medication_administration_search()
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
    medication_administration_service: MedicationAdministrationService,
):
    search_url, fhir_base = search_urls(request, "search_medication_administrations")
    (
        search_request,
        rows,
        total,
        included,
    ) = await medication_administration_service.search_medication_administrations(
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
    operation_id="search_medication_administrations",
    summary="Search MedicationAdministration resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_medication_administrations(
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_administration", "read")),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search MedicationAdministration resources",
        extra={"event": "route.search_medication_administrations"},
    )
    return await _search(
        request, get_query(request), actor, medication_administration_service
    )


@router.post(
    "/_search",
    operation_id="search_medication_administrations_post",
    summary="Search MedicationAdministration resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_medication_administrations_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("medication_administration", "read")),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    logger.info(
        "Search MedicationAdministration resources (POST _search)",
        extra={"event": "route.search_medication_administrations_post"},
    )
    return await _search(
        request, await post_query(request), actor, medication_administration_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{medication_administration_id}",
    operation_id="get_medication_administration_by_id",
    summary="Retrieve a MedicationAdministration resource by public medication_administration_id",
    description=(
        "Scoped to the caller's own org — get_medication_administration_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_medication_administration(
    request: Request,
    medication_administration_id: int = Path(
        ..., ge=1, description="Public medication_administration identifier."
    ),
    actor: AuthUser = Depends(require_permission("medication_administration", "read")),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    logger.info(
        "Retrieve a MedicationAdministration resource by public medication_administration_id",
        extra={
            "event": "route.get_medication_administration_by_id",
            "medication_administration_id": medication_administration_id,
        },
    )
    medication_administration = (
        await medication_administration_service.get_medication_administration_scoped(
            medication_administration_id, actor.org_id
        )
    )
    return fhir_response(
        medication_administration_service._to_fhir(medication_administration)
    )


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{medication_administration_id}",
    operation_id="patch_medication_administration",
    summary="Update a MedicationAdministration resource",
    description=(
        "The request body is a partial FHIR R4 MedicationAdministration (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, instantiates, partOf, statusReason, supportingInformation, performer, reasonCode, "
        "reasonReference, device, note, eventHistory - even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `context`, `category`, `effective[x]`, `request` or `dosage` replaces the whole "
        "value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_medication_administration() raises NotFoundError (404, not "
        "403 — avoids leaking that a MedicationAdministration with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_administration(
    payload: MedicationAdministrationPatchSchema,
    request: Request,
    medication_administration_id: int = Path(
        ..., ge=1, description="Public medication_administration identifier."
    ),
    actor: AuthUser = Depends(
        require_permission("medication_administration", "update")
    ),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_medication_administration()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a MedicationAdministration resource",
        extra={
            "event": "route.patch_medication_administration",
            "medication_administration_id": medication_administration_id,
        },
    )
    log_payload(logger, "medication_administration.patch.payload", payload)
    updated = await medication_administration_service.patch_medication_administration(
        medication_administration_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(medication_administration_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{medication_administration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_medication_administration",
    summary="Delete a MedicationAdministration resource",
    description=(
        "Permanently deletes the MedicationAdministration and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "medication_administration exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_medication_administration(
    medication_administration_id: int = Path(
        ..., ge=1, description="Public medication_administration identifier."
    ),
    actor: AuthUser = Depends(
        require_permission("medication_administration", "delete")
    ),
    medication_administration_service: MedicationAdministrationService = Depends(
        get_medication_administration_service
    ),
):
    """delete_medication_administration() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a MedicationAdministration resource",
        extra={
            "event": "route.delete_medication_administration",
            "medication_administration_id": medication_administration_id,
        },
    )
    await medication_administration_service.delete_medication_administration(
        medication_administration_id, org_id=actor.org_id
    )
