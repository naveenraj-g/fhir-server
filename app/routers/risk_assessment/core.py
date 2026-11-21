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
from app.di.dependencies.risk_assessment import get_risk_assessment_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.risk_assessment.search import risk_assessment_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.risk_assessment import RiskAssessmentCreateSchema, RiskAssessmentPatchSchema
from app.services.risk_assessment import RiskAssessmentService

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

# RiskAssessment always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_risk_assessment",
    summary="Create a new RiskAssessment resource",
    description=(
        "Records an assessment of the likely outcome(s) for a patient or other subject, and the likelihood "
        "of each outcome. The request body is a FHIR R4 RiskAssessment resource (camelCase, nested "
        "datatypes — https://www.hl7.org/fhir/R4/riskassessment.html); every supplied element (identifier, "
        "basedOn, parent, status, method, code, subject, encounter, occurrence[x], condition, performer, "
        "reasonCode, reasonReference, basis, prediction, mitigation, note) is stored as sent. R4 requires "
        "`status` and `subject`, and rules ras-1 / ras-2 (a probability is a percentage <= 100). "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>` subject, `Encounter/<id>`, `Condition/<id>`, a Practitioner or PractitionerRole "
        "performer, a Condition or DiagnosticReport reason, a note author (Practitioner, PractitionerRole, "
        "Patient, RelatedPerson, Organization) and `identifier.assigner` are rejected with 422 if they do not "
        "exist in the caller's org; a Group subject, a Device performer, basedOn, parent, basis, an Observation "
        "or DocumentReference reason, an absolute URL or a logical reference is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_risk_assessment(
    payload: RiskAssessmentCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("risk_assessment", "create")),
    risk_assessment_service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new RiskAssessment resource",
        extra={"event": "route.create_risk_assessment"},
    )
    log_payload(logger, "risk_assessment.create.payload", payload)
    risk_assessment = await risk_assessment_service.create_risk_assessment(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        risk_assessment_service._to_fhir(risk_assessment),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# RiskAssessment search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = risk_assessment_search()
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
    risk_assessment_service: RiskAssessmentService,
):
    search_url, fhir_base = search_urls(request, "search_risk_assessments")
    (
        search_request,
        rows,
        total,
        included,
    ) = await risk_assessment_service.search_risk_assessments(
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
    operation_id="search_risk_assessments",
    summary="Search RiskAssessment resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_risk_assessments(
    request: Request,
    actor: AuthUser = Depends(require_permission("risk_assessment", "read")),
    risk_assessment_service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search RiskAssessment resources",
        extra={"event": "route.search_risk_assessments"},
    )
    return await _search(request, get_query(request), actor, risk_assessment_service)


@router.post(
    "/_search",
    operation_id="search_risk_assessments_post",
    summary="Search RiskAssessment resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_risk_assessments_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("risk_assessment", "read")),
    risk_assessment_service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    logger.info(
        "Search RiskAssessment resources (POST _search)",
        extra={"event": "route.search_risk_assessments_post"},
    )
    return await _search(request, await post_query(request), actor, risk_assessment_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{risk_assessment_id}",
    operation_id="get_risk_assessment_by_id",
    summary="Retrieve an RiskAssessment resource by public risk_assessment_id",
    description=(
        "Scoped to the caller's own org — get_risk_assessment_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_risk_assessment(
    request: Request,
    risk_assessment_id: int = Path(
        ..., ge=1, description="Public risk_assessment identifier."
    ),
    actor: AuthUser = Depends(require_permission("risk_assessment", "read")),
    risk_assessment_service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    logger.info(
        "Retrieve an RiskAssessment resource by public risk_assessment_id",
        extra={
            "event": "route.get_risk_assessment_by_id",
            "risk_assessment_id": risk_assessment_id,
        },
    )
    risk_assessment = await risk_assessment_service.get_risk_assessment_scoped(
        risk_assessment_id, actor.org_id
    )
    return fhir_response(risk_assessment_service._to_fhir(risk_assessment))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{risk_assessment_id}",
    operation_id="patch_risk_assessment",
    summary="Update an RiskAssessment resource",
    description=(
        "The request body is a partial FHIR R4 RiskAssessment (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, reasonCode, reasonReference, basis, prediction, note — even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `performer` or `method` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_risk_assessment() raises NotFoundError (404, not "
        "403 — avoids leaking that a RiskAssessment with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_risk_assessment(
    payload: RiskAssessmentPatchSchema,
    request: Request,
    risk_assessment_id: int = Path(
        ..., ge=1, description="Public risk_assessment identifier."
    ),
    actor: AuthUser = Depends(require_permission("risk_assessment", "update")),
    risk_assessment_service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_risk_assessment()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update an RiskAssessment resource",
        extra={"event": "route.patch_risk_assessment", "risk_assessment_id": risk_assessment_id},
    )
    log_payload(logger, "risk_assessment.patch.payload", payload)
    updated = await risk_assessment_service.patch_risk_assessment(
        risk_assessment_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(risk_assessment_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{risk_assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_risk_assessment",
    summary="Delete an RiskAssessment resource",
    description=(
        "Permanently deletes the RiskAssessment and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "risk_assessment exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_risk_assessment(
    risk_assessment_id: int = Path(
        ..., ge=1, description="Public risk_assessment identifier."
    ),
    actor: AuthUser = Depends(require_permission("risk_assessment", "delete")),
    risk_assessment_service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    """delete_risk_assessment() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an RiskAssessment resource",
        extra={
            "event": "route.delete_risk_assessment",
            "risk_assessment_id": risk_assessment_id,
        },
    )
    await risk_assessment_service.delete_risk_assessment(risk_assessment_id, org_id=actor.org_id)
