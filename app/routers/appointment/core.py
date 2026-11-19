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
from app.di.dependencies.appointment import get_appointment_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.appointment.search import appointment_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.appointment import AppointmentCreateSchema, AppointmentPatchSchema
from app.services.appointment import AppointmentService

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

# Appointment always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_appointment",
    summary="Create a new Appointment resource",
    description=(
        "Books a healthcare event among patient(s), practitioner(s), related person(s) and/or device(s) "
        "for a specific date/time. The request body is a FHIR R4 Appointment resource (camelCase, nested "
        "datatypes — https://www.hl7.org/fhir/R4/appointment.html); the appointment and every supplied "
        "element (identifier, status, serviceCategory, serviceType, specialty, appointmentType, "
        "reasonCode, reasonReference, start, end, slot, participant, ...) are written atomically in one "
        "DB transaction. R4 requires `status` and at least one `participant` (each with a `status`). The "
        "body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that isn't FHIR at all is rejected with 422. "
        "A relative `Slot/<id>`, a participant actor that is a Patient, Practitioner, PractitionerRole, "
        "HealthcareService or Location, and `identifier.assigner` are rejected with 422 if they don't exist "
        "in the caller's org; other references (RelatedPerson, Device, ServiceRequest, Condition, ...) are "
        "stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_appointment(
    payload: AppointmentCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("appointment", "create")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new Appointment resource",
        extra={"event": "route.create_appointment"},
    )
    log_payload(logger, "appointment.create.payload", payload)
    appointment = await appointment_service.create_appointment(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        appointment_service._to_fhir(appointment),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Appointment search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = appointment_search()
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
    appointment_service: AppointmentService,
):
    search_url, fhir_base = search_urls(request, "search_appointments")
    (
        search_request,
        rows,
        total,
        included,
    ) = await appointment_service.search_appointments(
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
    operation_id="search_appointments",
    summary="Search Appointment resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_appointments(
    request: Request,
    actor: AuthUser = Depends(require_permission("appointment", "read")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Appointment resources",
        extra={"event": "route.search_appointments"},
    )
    return await _search(request, get_query(request), actor, appointment_service)


@router.post(
    "/_search",
    operation_id="search_appointments_post",
    summary="Search Appointment resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_appointments_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("appointment", "read")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    logger.info(
        "Search Appointment resources (POST _search)",
        extra={"event": "route.search_appointments_post"},
    )
    return await _search(request, await post_query(request), actor, appointment_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{appointment_id}",
    operation_id="get_appointment_by_id",
    summary="Retrieve an Appointment resource by public appointment_id",
    description=(
        "Scoped to the caller's own org — get_appointment_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_appointment(
    request: Request,
    appointment_id: int = Path(
        ..., ge=1, description="Public appointment identifier."
    ),
    actor: AuthUser = Depends(require_permission("appointment", "read")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    logger.info(
        "Retrieve an Appointment resource by public appointment_id",
        extra={
            "event": "route.get_appointment_by_id",
            "appointment_id": appointment_id,
        },
    )
    appointment = await appointment_service.get_appointment_scoped(
        appointment_id, actor.org_id
    )
    return fhir_response(appointment_service._to_fhir(appointment))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{appointment_id}",
    operation_id="patch_appointment",
    summary="Update an Appointment resource",
    description=(
        "The request body is a partial FHIR R4 Appointment (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. Every supplied "
        "list (identifier, serviceCategory, serviceType, specialty, reasonCode, slot, participant — even "
        "`[]`) atomically replaces the stored entries, a supplied `appointmentType` or `cancelationReason` "
        "replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_appointment() raises NotFoundError (404, not "
        "403 — avoids leaking that an appointment with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_appointment(
    payload: AppointmentPatchSchema,
    request: Request,
    appointment_id: int = Path(
        ..., ge=1, description="Public appointment identifier."
    ),
    actor: AuthUser = Depends(require_permission("appointment", "update")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_appointment()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an Appointment resource",
        extra={"event": "route.patch_appointment", "appointment_id": appointment_id},
    )
    log_payload(logger, "appointment.patch.payload", payload)
    updated = await appointment_service.patch_appointment(
        appointment_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(appointment_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_appointment",
    summary="Delete an Appointment resource",
    description=(
        "Permanently deletes the Appointment and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "appointment exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_appointment(
    appointment_id: int = Path(
        ..., ge=1, description="Public appointment identifier."
    ),
    actor: AuthUser = Depends(require_permission("appointment", "delete")),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """delete_appointment() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an Appointment resource",
        extra={
            "event": "route.delete_appointment",
            "appointment_id": appointment_id,
        },
    )
    await appointment_service.delete_appointment(appointment_id, org_id=actor.org_id)
