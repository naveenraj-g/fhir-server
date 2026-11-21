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
from app.di.dependencies.detected_issue import get_detected_issue_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.detected_issue.search import detected_issue_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.detected_issue import (
    DetectedIssueCreateSchema,
    DetectedIssuePatchSchema,
)
from app.services.detected_issue import DetectedIssueService

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

# DetectedIssue always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_detected_issue",
    summary="Create a new DetectedIssue resource",
    description=(
        "Records an actual or potential clinical problem detected for a patient — such as a drug "
        "interaction or duplicate therapy — with its evidence and the steps taken to mitigate it. The "
        "request body is a FHIR R4 DetectedIssue resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/detectedissue.html); every supplied element (identifier, status, code, "
        "severity, patient, identified[x], author, implicated, evidence, detail, reference, mitigation) is "
        "stored as sent. R4 requires `status`. "
        "The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>`, a Practitioner or PractitionerRole author or mitigation author, an `implicated` or "
        "`evidence.detail` reference to a resource this server holds, and `identifier.assigner` are rejected "
        "with 422 if they do not exist in the caller's org; a Device author, a reference to a resource not "
        "held here (e.g. a MedicationRequest), an absolute URL or a logical reference is stored as sent. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_detected_issue(
    payload: DetectedIssueCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("detected_issue", "create")),
    detected_issue_service: DetectedIssueService = Depends(get_detected_issue_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new DetectedIssue resource",
        extra={"event": "route.create_detected_issue"},
    )
    log_payload(logger, "detected_issue.create.payload", payload)
    detected_issue = await detected_issue_service.create_detected_issue(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        detected_issue_service._to_fhir(detected_issue),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# DetectedIssue search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = detected_issue_search()
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
    detected_issue_service: DetectedIssueService,
):
    search_url, fhir_base = search_urls(request, "search_detected_issues")
    (
        search_request,
        rows,
        total,
        included,
    ) = await detected_issue_service.search_detected_issues(
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
    operation_id="search_detected_issues",
    summary="Search DetectedIssue resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_detected_issues(
    request: Request,
    actor: AuthUser = Depends(require_permission("detected_issue", "read")),
    detected_issue_service: DetectedIssueService = Depends(get_detected_issue_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search DetectedIssue resources",
        extra={"event": "route.search_detected_issues"},
    )
    return await _search(request, get_query(request), actor, detected_issue_service)


@router.post(
    "/_search",
    operation_id="search_detected_issues_post",
    summary="Search DetectedIssue resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_detected_issues_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("detected_issue", "read")),
    detected_issue_service: DetectedIssueService = Depends(get_detected_issue_service),
):
    logger.info(
        "Search DetectedIssue resources (POST _search)",
        extra={"event": "route.search_detected_issues_post"},
    )
    return await _search(
        request, await post_query(request), actor, detected_issue_service
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{detected_issue_id}",
    operation_id="get_detected_issue_by_id",
    summary="Retrieve an DetectedIssue resource by public detected_issue_id",
    description=(
        "Scoped to the caller's own org — get_detected_issue_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_detected_issue(
    request: Request,
    detected_issue_id: int = Path(
        ..., ge=1, description="Public detected_issue identifier."
    ),
    actor: AuthUser = Depends(require_permission("detected_issue", "read")),
    detected_issue_service: DetectedIssueService = Depends(get_detected_issue_service),
):
    logger.info(
        "Retrieve an DetectedIssue resource by public detected_issue_id",
        extra={
            "event": "route.get_detected_issue_by_id",
            "detected_issue_id": detected_issue_id,
        },
    )
    detected_issue = await detected_issue_service.get_detected_issue_scoped(
        detected_issue_id, actor.org_id
    )
    return fhir_response(detected_issue_service._to_fhir(detected_issue))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{detected_issue_id}",
    operation_id="patch_detected_issue",
    summary="Update a DetectedIssue resource",
    description=(
        "The request body is a partial FHIR R4 DetectedIssue (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, implicated, evidence, mitigation — even `[]`) atomically replaces the stored entries, a "
        "supplied `patient`, `author` or `code` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_detected_issue() raises NotFoundError (404, not "
        "403 — avoids leaking that a DetectedIssue with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_detected_issue(
    payload: DetectedIssuePatchSchema,
    request: Request,
    detected_issue_id: int = Path(
        ..., ge=1, description="Public detected_issue identifier."
    ),
    actor: AuthUser = Depends(require_permission("detected_issue", "update")),
    detected_issue_service: DetectedIssueService = Depends(get_detected_issue_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_detected_issue()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a DetectedIssue resource",
        extra={
            "event": "route.patch_detected_issue",
            "detected_issue_id": detected_issue_id,
        },
    )
    log_payload(logger, "detected_issue.patch.payload", payload)
    updated = await detected_issue_service.patch_detected_issue(
        detected_issue_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(detected_issue_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{detected_issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_detected_issue",
    summary="Delete an DetectedIssue resource",
    description=(
        "Permanently deletes the DetectedIssue and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "detected_issue exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_detected_issue(
    detected_issue_id: int = Path(
        ..., ge=1, description="Public detected_issue identifier."
    ),
    actor: AuthUser = Depends(require_permission("detected_issue", "delete")),
    detected_issue_service: DetectedIssueService = Depends(get_detected_issue_service),
):
    """delete_detected_issue() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete an DetectedIssue resource",
        extra={
            "event": "route.delete_detected_issue",
            "detected_issue_id": detected_issue_id,
        },
    )
    await detected_issue_service.delete_detected_issue(
        detected_issue_id, org_id=actor.org_id
    )
