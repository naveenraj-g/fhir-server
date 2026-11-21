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
from app.di.dependencies.clinical_impression import get_clinical_impression_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.clinical_impression.search import clinical_impression_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.clinical_impression import ClinicalImpressionCreateSchema, ClinicalImpressionPatchSchema
from app.services.clinical_impression import ClinicalImpressionService

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

# ClinicalImpression always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_clinical_impression",
    summary="Create a new ClinicalImpression resource",
    description=(
        "Records a clinician's assessment of a patient's condition: the problems considered, the "
        "investigations done, the findings and the prognosis. The request body is a FHIR R4 "
        "ClinicalImpression resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/clinicalimpression.html); every supplied element (identifier, status, "
        "statusReason, code, description, subject, encounter, effective[x], date, assessor, previous, problem, "
        "investigation, protocol, summary, finding, prognosisCodeableConcept, prognosisReference, "
        "supportingInfo, note) is stored as sent. R4 requires `status` and `subject`. "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>` subject, `Encounter/<id>`, a Practitioner or PractitionerRole assessor, `previous` "
        "(ClinicalImpression), a Condition or AllergyIntolerance problem, a RiskAssessment, "
        "FamilyMemberHistory or DiagnosticReport investigation item, a Condition finding, a RiskAssessment "
        "prognosis, a supportingInfo that is a resource this server holds, a note author (Practitioner, "
        "PractitionerRole, Patient, RelatedPerson, Organization) and `identifier.assigner` are rejected with 422 "
        "if they do not exist in the caller's org; a Group subject, an Observation, Media, ImagingStudy or "
        "QuestionnaireResponse investigation, an Observation or Media finding, an absolute URL or a logical "
        "reference is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_clinical_impression(
    payload: ClinicalImpressionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("clinical_impression", "create")),
    clinical_impression_service: ClinicalImpressionService = Depends(get_clinical_impression_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new ClinicalImpression resource",
        extra={"event": "route.create_clinical_impression"},
    )
    log_payload(logger, "clinical_impression.create.payload", payload)
    clinical_impression = await clinical_impression_service.create_clinical_impression(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        clinical_impression_service._to_fhir(clinical_impression),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# ClinicalImpression search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = clinical_impression_search()
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
    clinical_impression_service: ClinicalImpressionService,
):
    search_url, fhir_base = search_urls(request, "search_clinical_impressions")
    (
        search_request,
        rows,
        total,
        included,
    ) = await clinical_impression_service.search_clinical_impressions(
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
    operation_id="search_clinical_impressions",
    summary="Search ClinicalImpression resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_clinical_impressions(
    request: Request,
    actor: AuthUser = Depends(require_permission("clinical_impression", "read")),
    clinical_impression_service: ClinicalImpressionService = Depends(get_clinical_impression_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search ClinicalImpression resources",
        extra={"event": "route.search_clinical_impressions"},
    )
    return await _search(request, get_query(request), actor, clinical_impression_service)


@router.post(
    "/_search",
    operation_id="search_clinical_impressions_post",
    summary="Search ClinicalImpression resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_clinical_impressions_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("clinical_impression", "read")),
    clinical_impression_service: ClinicalImpressionService = Depends(get_clinical_impression_service),
):
    logger.info(
        "Search ClinicalImpression resources (POST _search)",
        extra={"event": "route.search_clinical_impressions_post"},
    )
    return await _search(request, await post_query(request), actor, clinical_impression_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{clinical_impression_id}",
    operation_id="get_clinical_impression_by_id",
    summary="Retrieve an ClinicalImpression resource by public clinical_impression_id",
    description=(
        "Scoped to the caller's own org — get_clinical_impression_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_clinical_impression(
    request: Request,
    clinical_impression_id: int = Path(
        ..., ge=1, description="Public clinical_impression identifier."
    ),
    actor: AuthUser = Depends(require_permission("clinical_impression", "read")),
    clinical_impression_service: ClinicalImpressionService = Depends(get_clinical_impression_service),
):
    logger.info(
        "Retrieve an ClinicalImpression resource by public clinical_impression_id",
        extra={
            "event": "route.get_clinical_impression_by_id",
            "clinical_impression_id": clinical_impression_id,
        },
    )
    clinical_impression = await clinical_impression_service.get_clinical_impression_scoped(
        clinical_impression_id, actor.org_id
    )
    return fhir_response(clinical_impression_service._to_fhir(clinical_impression))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{clinical_impression_id}",
    operation_id="patch_clinical_impression",
    summary="Update a ClinicalImpression resource",
    description=(
        "The request body is a partial FHIR R4 ClinicalImpression (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, problem, investigation, finding, prognosisCodeableConcept, supportingInfo, note — even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `assessor` or `code` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_clinical_impression() raises NotFoundError (404, not "
        "403 — avoids leaking that a ClinicalImpression with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_clinical_impression(
    payload: ClinicalImpressionPatchSchema,
    request: Request,
    clinical_impression_id: int = Path(
        ..., ge=1, description="Public clinical_impression identifier."
    ),
    actor: AuthUser = Depends(require_permission("clinical_impression", "update")),
    clinical_impression_service: ClinicalImpressionService = Depends(get_clinical_impression_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_clinical_impression()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a ClinicalImpression resource",
        extra={"event": "route.patch_clinical_impression", "clinical_impression_id": clinical_impression_id},
    )
    log_payload(logger, "clinical_impression.patch.payload", payload)
    updated = await clinical_impression_service.patch_clinical_impression(
        clinical_impression_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(clinical_impression_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{clinical_impression_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_clinical_impression",
    summary="Delete an ClinicalImpression resource",
    description=(
        "Permanently deletes the ClinicalImpression and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "clinical_impression exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_clinical_impression(
    clinical_impression_id: int = Path(
        ..., ge=1, description="Public clinical_impression identifier."
    ),
    actor: AuthUser = Depends(require_permission("clinical_impression", "delete")),
    clinical_impression_service: ClinicalImpressionService = Depends(get_clinical_impression_service),
):
    """delete_clinical_impression() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an ClinicalImpression resource",
        extra={
            "event": "route.delete_clinical_impression",
            "clinical_impression_id": clinical_impression_id,
        },
    )
    await clinical_impression_service.delete_clinical_impression(clinical_impression_id, org_id=actor.org_id)
