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
from app.di.dependencies.procedure import get_procedure_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.procedure.search import procedure_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.procedure import ProcedureCreateSchema, ProcedurePatchSchema
from app.services.procedure import ProcedureService

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

# Procedure always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_procedure",
    summary="Create a new Procedure resource",
    description=(
        "Records an action that is or was performed on or for a patient, practitioner, device, organization or "
        "location — a surgery, a diagnostic procedure, a counselling session. The request body is a FHIR R4 "
        "Procedure resource (camelCase, nested datatypes — https://www.hl7.org/fhir/R4/procedure.html); every "
        "supplied element (identifier, instantiatesCanonical, instantiatesUri, basedOn, partOf, status, "
        "statusReason, category, code, subject, encounter, performed[x], recorder, asserter, performer, "
        "location, reasonCode, reasonReference, bodySite, outcome, report, complication, complicationDetail, "
        "followUp, note, focalDevice, usedReference, usedCode) is stored as sent. R4 requires `status` and "
        "`subject`. The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>` subject, `Encounter/<id>`, `Location/<id>`, a recorder/asserter (Practitioner, "
        "PractitionerRole, Patient, RelatedPerson), a performer actor (Practitioner, PractitionerRole, Organization, "
        "Patient, RelatedPerson), `partOf` and `reasonReference` (Procedure, Condition), `complicationDetail`, a "
        "note author and `identifier.assigner` are rejected with 422 if they do not exist in the caller's org; an "
        "absolute URL, a Group subject, a Device or a logical reference is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_procedure(
    payload: ProcedureCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("procedure", "create")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new Procedure resource",
        extra={"event": "route.create_procedure"},
    )
    log_payload(logger, "procedure.create.payload", payload)
    procedure = await procedure_service.create_procedure(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        procedure_service._to_fhir(procedure),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Procedure search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = procedure_search()
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
    procedure_service: ProcedureService,
):
    search_url, fhir_base = search_urls(request, "search_procedures")
    (
        search_request,
        rows,
        total,
        included,
    ) = await procedure_service.search_procedures(
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
    operation_id="search_procedures",
    summary="Search Procedure resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_procedures(
    request: Request,
    actor: AuthUser = Depends(require_permission("procedure", "read")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Procedure resources",
        extra={"event": "route.search_procedures"},
    )
    return await _search(request, get_query(request), actor, procedure_service)


@router.post(
    "/_search",
    operation_id="search_procedures_post",
    summary="Search Procedure resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_procedures_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("procedure", "read")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    logger.info(
        "Search Procedure resources (POST _search)",
        extra={"event": "route.search_procedures_post"},
    )
    return await _search(request, await post_query(request), actor, procedure_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{procedure_id}",
    operation_id="get_procedure_by_id",
    summary="Retrieve a Procedure resource by public procedure_id",
    description=(
        "Scoped to the caller's own org — get_procedure_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_procedure(
    request: Request,
    procedure_id: int = Path(
        ..., ge=1, description="Public procedure identifier."
    ),
    actor: AuthUser = Depends(require_permission("procedure", "read")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    logger.info(
        "Retrieve a Procedure resource by public procedure_id",
        extra={
            "event": "route.get_procedure_by_id",
            "procedure_id": procedure_id,
        },
    )
    procedure = await procedure_service.get_procedure_scoped(
        procedure_id, actor.org_id
    )
    return fhir_response(procedure_service._to_fhir(procedure))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{procedure_id}",
    operation_id="patch_procedure",
    summary="Update a Procedure resource",
    description=(
        "The request body is a partial FHIR R4 Procedure (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, performer, reasonCode, reasonReference, bodySite, note — even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `code` or `outcome` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_procedure() raises NotFoundError (404, not "
        "403 — avoids leaking that a procedure with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_procedure(
    payload: ProcedurePatchSchema,
    request: Request,
    procedure_id: int = Path(
        ..., ge=1, description="Public procedure identifier."
    ),
    actor: AuthUser = Depends(require_permission("procedure", "update")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_procedure()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Procedure resource",
        extra={"event": "route.patch_procedure", "procedure_id": procedure_id},
    )
    log_payload(logger, "procedure.patch.payload", payload)
    updated = await procedure_service.patch_procedure(
        procedure_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(procedure_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{procedure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_procedure",
    summary="Delete a Procedure resource",
    description=(
        "Permanently deletes the Procedure and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "procedure exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_procedure(
    procedure_id: int = Path(
        ..., ge=1, description="Public procedure identifier."
    ),
    actor: AuthUser = Depends(require_permission("procedure", "delete")),
    procedure_service: ProcedureService = Depends(get_procedure_service),
):
    """delete_procedure() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a Procedure resource",
        extra={
            "event": "route.delete_procedure",
            "procedure_id": procedure_id,
        },
    )
    await procedure_service.delete_procedure(procedure_id, org_id=actor.org_id)
