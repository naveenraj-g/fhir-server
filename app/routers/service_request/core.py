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
from app.di.dependencies.service_request import get_service_request_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.service_request.search import service_request_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.service_request import (
    ServiceRequestCreateSchema,
    ServiceRequestPatchSchema,
)
from app.services.service_request import ServiceRequestService

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

# ServiceRequest always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_service_request",
    summary="Create a new ServiceRequest resource",
    description=(
        "Records a request for a procedure, diagnostic investigation or other service to be performed "
        "for a patient, group, location or device — a lab order, an imaging request, a referral. The "
        "request body is a FHIR R4 ServiceRequest resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/servicerequest.html); every supplied element (identifier, "
        "instantiatesCanonical, instantiatesUri, basedOn, replaces, requisition, status, intent, category, "
        "priority, doNotPerform, code, orderDetail, quantity[x], subject, encounter, occurrence[x], "
        "asNeeded[x], authoredOn, requester, performerType, performer, locationCode, locationReference, "
        "reasonCode, reasonReference, insurance, supportingInfo, specimen, bodySite, note, "
        "patientInstruction, relevantHistory) is stored as sent. R4 requires `status`, `intent` and "
        "`subject`. The body is checked against base FHIR R4: any valid R4 element is accepted and stored as "
        "sent (server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. "
        "A relative `Patient/<id>` or `Location/<id>` subject, `Encounter/<id>`, a requester or performer of "
        "a rebuilt type (Practitioner, PractitionerRole, Organization, HealthcareService, Patient, "
        "RelatedPerson), `basedOn` / `replaces` (ServiceRequest), `specimen`, `locationReference`, "
        "`reasonReference` (Condition, Observation, DiagnosticReport), `supportingInfo` (any rebuilt "
        "resource), a note author and every identifier's `assigner` are rejected with 422 if they do not "
        "exist in the caller's org; a Group or Device subject, a CareTeam or Device performer, "
        "CarePlan / MedicationRequest `basedOn`, a DocumentReference reason, `insurance`, "
        "`relevantHistory`, an absolute URL or a logical reference is stored as sent. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_service_request(
    payload: ServiceRequestCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("service_request", "create")),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new ServiceRequest resource",
        extra={"event": "route.create_service_request"},
    )
    log_payload(logger, "service_request.create.payload", payload)
    service_request = await service_request_service.create_service_request(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        service_request_service._to_fhir(service_request),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# ServiceRequest search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = service_request_search()
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
    service_request_service: ServiceRequestService,
):
    search_url, fhir_base = search_urls(request, "search_service_requests")
    (
        search_request,
        rows,
        total,
        included,
    ) = await service_request_service.search_service_requests(
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
    operation_id="search_service_requests",
    summary="Search ServiceRequest resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_service_requests(
    request: Request,
    actor: AuthUser = Depends(require_permission("service_request", "read")),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search ServiceRequest resources",
        extra={"event": "route.search_service_requests"},
    )
    return await _search(request, get_query(request), actor, service_request_service)


@router.post(
    "/_search",
    operation_id="search_service_requests_post",
    summary="Search ServiceRequest resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_service_requests_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("service_request", "read")),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    logger.info(
        "Search ServiceRequest resources (POST _search)",
        extra={"event": "route.search_service_requests_post"},
    )
    return await _search(
        request, await post_query(request), actor, service_request_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{service_request_id}",
    operation_id="get_service_request_by_id",
    summary="Retrieve a ServiceRequest resource by public service_request_id",
    description=(
        "Scoped to the caller's own org — get_service_request_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_service_request(
    request: Request,
    service_request_id: int = Path(
        ..., ge=1, description="Public service_request identifier."
    ),
    actor: AuthUser = Depends(require_permission("service_request", "read")),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    logger.info(
        "Retrieve a ServiceRequest resource by public service_request_id",
        extra={
            "event": "route.get_service_request_by_id",
            "service_request_id": service_request_id,
        },
    )
    service_request = await service_request_service.get_service_request_scoped(
        service_request_id, actor.org_id
    )
    return fhir_response(service_request_service._to_fhir(service_request))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{service_request_id}",
    operation_id="patch_service_request",
    summary="Update a ServiceRequest resource",
    description=(
        "The request body is a partial FHIR R4 ServiceRequest (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, category, performer, specimen, reasonCode, bodySite, note — even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `code` or `requisition` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_service_request() raises NotFoundError (404, not "
        "403 — avoids leaking that a service_request with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_service_request(
    payload: ServiceRequestPatchSchema,
    request: Request,
    service_request_id: int = Path(
        ..., ge=1, description="Public service_request identifier."
    ),
    actor: AuthUser = Depends(require_permission("service_request", "update")),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_service_request()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a ServiceRequest resource",
        extra={
            "event": "route.patch_service_request",
            "service_request_id": service_request_id,
        },
    )
    log_payload(logger, "service_request.patch.payload", payload)
    updated = await service_request_service.patch_service_request(
        service_request_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(service_request_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{service_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_service_request",
    summary="Delete a ServiceRequest resource",
    description=(
        "Permanently deletes the ServiceRequest and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "service_request exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_service_request(
    service_request_id: int = Path(
        ..., ge=1, description="Public service_request identifier."
    ),
    actor: AuthUser = Depends(require_permission("service_request", "delete")),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    """delete_service_request() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a ServiceRequest resource",
        extra={
            "event": "route.delete_service_request",
            "service_request_id": service_request_id,
        },
    )
    await service_request_service.delete_service_request(
        service_request_id, org_id=actor.org_id
    )
