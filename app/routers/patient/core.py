from fastapi import APIRouter, Depends, Path, Query, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.config import settings
from app.core.content_negotiation import (
    FHIRJSONResponse,
    fhir_response,
    require_fhir_json,
)
from app.core.logging import get_logger, log_payload
from app.core.schema_utils import inline_schema
from app.di.dependencies.patient import get_patient_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.patient.search import patient_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.patient import (
    PatientCreateSchema,
    PatientPatchSchema,
    PatientUserLinkInput,
    PatientUserLinkResponse,
)
from app.services.patient import PatientService

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

# Patient always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_patient",
    summary="Create a new Patient resource",
    description=(
        "Records demographics and other administrative information about an individual receiving "
        "care. The request body is a FHIR R4 Patient resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/patient.html); the patient and every supplied element "
        "(identifier, name, telecom, address, maritalStatus, contact, communication, "
        "generalPractitioner, managingOrganization, link, ...) are written atomically in one DB "
        "transaction. The body is checked against base FHIR R4: any valid R4 element is accepted "
        "and stored as sent (server-managed `id`/`meta` are ignored); a key that isn't FHIR at all "
        "is rejected with 422. `managingOrganization`, `generalPractitioner` "
        "(Practitioner | PractitionerRole | Organization), `link.other` (Patient), "
        "`contact.organization` and `identifier.assigner` may reference resources on this server "
        "(e.g. `{\"reference\": \"Organization/190001\"}`) — rejected with 422 if a relative "
        "reference doesn't exist in the caller's org. The record starts unlinked: the end-user it "
        "belongs to (what `GET /me` scopes to) is linked afterwards with `PUT /{patient_id}/user`, "
        "or straight away with `?link_me=true` when the caller is creating their own record "
        "(self-signup). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_patient(
    payload: PatientCreateSchema,
    request: Request,
    link_me: bool = Query(
        False,
        description="Self-signup: also link the new record to the caller's own user (the JWT `sub`), so "
        "`GET /me` works straight away. 422 if that user is already linked to a patient in this org. "
        "Leave unset when creating a record for someone else and link it afterwards with `PUT /{patient_id}/user`.",
    ),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403). Create never links an end-user (see
    link_patient_user)."""
    logger.info(
        "Create a new Patient resource",
        extra={"event": "route.create_patient"},
    )
    log_payload(logger, "patient.create.payload", payload)
    patient = await patient_service.create_patient(
        payload, actor.org_id, actor.sub, body=await request.json(),
        link_user_id=actor.sub if link_me else None,
    )
    return fhir_response(
        patient_service._to_fhir(patient),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Patient search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = patient_search()
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
    patient_service: PatientService,
    route_name: str,
    user_id: str | None = None,
):
    # fhir_base always comes from the main search route (`/me` sits one
    # segment deeper); the paging links point back at the route that ran.
    _, fhir_base = search_urls(request, "search_patients")
    search_url = str(request.url_for(route_name))
    (
        search_request,
        rows,
        total,
        included,
    ) = await patient_service.search_patients(
        query,
        actor.org_id,
        strict=strict_handling(request),
        fhir_base=fhir_base,
        user_id=user_id,
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
    operation_id="search_patients",
    summary="Search Patient resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_patients(
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Patient resources",
        extra={"event": "route.search_patients"},
    )
    return await _search(
        request, get_query(request), actor, patient_service, "search_patients"
    )


@router.post(
    "/_search",
    operation_id="search_patients_post",
    summary="Search Patient resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_patients_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "Search Patient resources (POST _search)",
        extra={"event": "route.search_patients_post"},
    )
    return await _search(
        request,
        await post_query(request),
        actor,
        patient_service,
        "search_patients",
    )


# ── Me (must come before /{patient_id}) ────────────────────────────


@router.get(
    "/me",
    operation_id="search_my_patients",
    summary="Search Patient resources owned by the authenticated end-user",
    description=(
        "Same search as `GET /` (every parameter, modifier and result parameter), always "
        "additionally restricted to the authenticated end-user's own records — those linked "
        "to the token's `sub` (see `PUT /{patient_id}/user`) — on top of the caller's own org. "
        + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_my_patients(
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "Search Patient resources owned by the authenticated end-user",
        extra={"event": "route.search_my_patients"},
    )
    return await _search(
        request,
        get_query(request),
        actor,
        patient_service,
        "search_my_patients",
        user_id=actor.sub,
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{patient_id}",
    operation_id="get_patient_by_id",
    summary="Retrieve a Patient resource by public patient_id",
    description=(
        "Scoped to the caller's own org — get_patient_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_patient(
    request: Request,
    patient_id: int = Path(
        ..., ge=1, description="Public patient identifier."
    ),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "Retrieve a Patient resource by public patient_id",
        extra={
            "event": "route.get_patient_by_id",
            "patient_id": patient_id,
        },
    )
    patient = await patient_service.get_patient_scoped(
        patient_id, actor.org_id
    )
    return fhir_response(patient_service._to_fhir(patient))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{patient_id}",
    operation_id="patch_patient",
    summary="Update a Patient resource",
    description=(
        "The request body is a partial FHIR R4 Patient (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. Every supplied "
        "list (identifier, name, telecom, address, photo, contact, communication, generalPractitioner, link — even "
        "`[]`) atomically replaces the stored entries, and `null` clears an element. "
        "Scoped to the caller's own org — patch_patient() raises NotFoundError (404, not "
        "403 — avoids leaking that a patient with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_patient(
    payload: PatientPatchSchema,
    request: Request,
    patient_id: int = Path(
        ..., ge=1, description="Public patient identifier."
    ),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_patient()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Patient resource",
        extra={"event": "route.patch_patient", "patient_id": patient_id},
    )
    log_payload(logger, "patient.patch.payload", payload)
    updated = await patient_service.patch_patient(
        patient_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(patient_service._to_fhir(updated))


# ── End-user link ────────────────────────────────────────────────────────
# Which IAM user acts as this patient. Not a FHIR element, so it is
# not in the resource body and not settable through create/patch — only
# here, behind its own permission (the equivalent of creating a Medplum
# ProjectMembership with `profile` = this patient).

_USER_LINK_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(PatientUserLinkResponse.model_json_schema())
            }
        }
    }
}


def _link_response(patient) -> JSONResponse:
    return JSONResponse(
        PatientUserLinkResponse(
            patient_id=patient.patient_id, user_id=patient.user_id
        ).model_dump()
    )


@router.get(
    "/{patient_id}/user",
    operation_id="get_patient_user_link",
    summary="Show which end-user is linked to a Patient",
    description=(
        "Returns the linked IAM user id, or `null` when the record is not linked. Not a FHIR "
        "resource (`application/json`). Scoped to the caller's own org like every other read."
    ),
    responses={**_USER_LINK_200, **_ERR_NOT_FOUND},
    response_class=JSONResponse,
)
async def get_patient_user_link(
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "Get a Patient end-user link",
        extra={"event": "route.get_patient_user_link", "patient_id": patient_id},
    )
    return _link_response(
        await patient_service.get_user_link(patient_id, actor.org_id)
    )


@router.put(
    "/{patient_id}/user",
    operation_id="link_patient_user",
    summary="Link an end-user to a Patient",
    description=(
        "Links the IAM user `user_id` (a JWT `sub`) to this patient, so that user's "
        "`GET /me` returns it. Replaces any previous link; linking the same user again is a "
        "no-op. A user can act as at most one patient per org (422 if already linked "
        "to another). Requires the separate `patient:link` permission — linking is how "
        "an onboarding/verification flow (or an admin) confirms that a person is this "
        "patient. Scoped to the caller's own org (404 across orgs)."
    ),
    responses={**_USER_LINK_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    response_class=JSONResponse,
)
async def link_patient_user(
    payload: PatientUserLinkInput,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "link")),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "Link an end-user to a Patient",
        extra={"event": "route.link_patient_user", "patient_id": patient_id},
    )
    return _link_response(
        await patient_service.link_user(
            patient_id, payload.user_id, actor.org_id, actor.sub
        )
    )


@router.delete(
    "/{patient_id}/user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="unlink_patient_user",
    summary="Remove the end-user link from a Patient",
    description=(
        "Clears the link; idempotent (204 whether or not it was linked). The Patient "
        "record itself is untouched. Requires `patient:link`. Scoped to the caller's own "
        "org (404 across orgs)."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def unlink_patient_user(
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "link")),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "Remove a Patient end-user link",
        extra={"event": "route.unlink_patient_user", "patient_id": patient_id},
    )
    await patient_service.unlink_user(patient_id, actor.org_id, actor.sub)


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient",
    summary="Delete a Patient resource",
    description=(
        "Permanently deletes the Patient and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "patient exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_patient(
    patient_id: int = Path(
        ..., ge=1, description="Public patient identifier."
    ),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_patient() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a Patient resource",
        extra={
            "event": "route.delete_patient",
            "patient_id": patient_id,
        },
    )
    await patient_service.delete_patient(patient_id, org_id=actor.org_id)
