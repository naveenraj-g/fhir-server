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
from app.di.dependencies.diagnostic_report import get_diagnostic_report_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.diagnostic_report.search import diagnostic_report_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.diagnostic_report import DiagnosticReportCreateSchema, DiagnosticReportPatchSchema
from app.services.diagnostic_report import DiagnosticReportService

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

# DiagnosticReport always responds with FHIR R4 JSON, whatever the Accept
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
    operation_id="create_diagnostic_report",
    summary="Create a new DiagnosticReport resource",
    description=(
        "Records the findings and interpretation of diagnostic tests performed on patients, groups of patients, "
        "devices, and locations — a laboratory report, an imaging report. The request body is a FHIR R4 "
        "DiagnosticReport resource (camelCase, nested datatypes — "
        "https://www.hl7.org/fhir/R4/diagnosticreport.html); every supplied element (identifier, basedOn, status, "
        "category, code, subject, encounter, effective[x], issued, performer, resultsInterpreter, specimen, result, "
        "imagingStudy, media, conclusion, conclusionCode, presentedForm) is stored as sent. R4 requires `status` "
        "and `code`. The body is checked against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that is not FHIR at all is rejected with 422. A relative "
        "`Patient/<id>` or `Location/<id>` subject, `Encounter/<id>`, a performer or results interpreter "
        "(Practitioner, PractitionerRole, Organization) and `identifier.assigner` are rejected with 422 if they do "
        "not exist in the caller's org; an absolute URL, a Group or Device subject, a CareTeam, basedOn, specimen, "
        "result, media or a logical reference is stored as sent. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_diagnostic_report(
    payload: DiagnosticReportCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("diagnostic_report", "create")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403)."""
    logger.info(
        "Create a new DiagnosticReport resource",
        extra={"event": "route.create_diagnostic_report"},
    )
    log_payload(logger, "diagnostic_report.create.payload", payload)
    diagnostic_report = await diagnostic_report_service.create_diagnostic_report(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        diagnostic_report_service._to_fhir(diagnostic_report),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# DiagnosticReport search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = diagnostic_report_search()
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
    diagnostic_report_service: DiagnosticReportService,
):
    search_url, fhir_base = search_urls(request, "search_diagnostic_reports")
    (
        search_request,
        rows,
        total,
        included,
    ) = await diagnostic_report_service.search_diagnostic_reports(
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
    operation_id="search_diagnostic_reports",
    summary="Search DiagnosticReport resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_diagnostic_reports(
    request: Request,
    actor: AuthUser = Depends(require_permission("diagnostic_report", "read")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search DiagnosticReport resources",
        extra={"event": "route.search_diagnostic_reports"},
    )
    return await _search(request, get_query(request), actor, diagnostic_report_service)


@router.post(
    "/_search",
    operation_id="search_diagnostic_reports_post",
    summary="Search DiagnosticReport resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_diagnostic_reports_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("diagnostic_report", "read")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info(
        "Search DiagnosticReport resources (POST _search)",
        extra={"event": "route.search_diagnostic_reports_post"},
    )
    return await _search(request, await post_query(request), actor, diagnostic_report_service)


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{diagnostic_report_id}",
    operation_id="get_diagnostic_report_by_id",
    summary="Retrieve a DiagnosticReport resource by public diagnostic_report_id",
    description=(
        "Scoped to the caller's own org — get_diagnostic_report_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_diagnostic_report(
    request: Request,
    diagnostic_report_id: int = Path(
        ..., ge=1, description="Public diagnostic_report identifier."
    ),
    actor: AuthUser = Depends(require_permission("diagnostic_report", "read")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    logger.info(
        "Retrieve a DiagnosticReport resource by public diagnostic_report_id",
        extra={
            "event": "route.get_diagnostic_report_by_id",
            "diagnostic_report_id": diagnostic_report_id,
        },
    )
    diagnostic_report = await diagnostic_report_service.get_diagnostic_report_scoped(
        diagnostic_report_id, actor.org_id
    )
    return fhir_response(diagnostic_report_service._to_fhir(diagnostic_report))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{diagnostic_report_id}",
    operation_id="patch_diagnostic_report",
    summary="Update a DiagnosticReport resource",
    description=(
        "The request body is a partial FHIR R4 DiagnosticReport (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. A supplied list "
        "(identifier, category, performer, result, specimen, media, conclusionCode — even `[]`) atomically replaces the stored entries, a "
        "supplied `subject`, `code` or `effectivePeriod` replaces the whole value, and `null` clears an element. "
        "Scoped to the caller's own org — patch_diagnostic_report() raises NotFoundError (404, not "
        "403 — avoids leaking that a diagnostic report with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_diagnostic_report(
    payload: DiagnosticReportPatchSchema,
    request: Request,
    diagnostic_report_id: int = Path(
        ..., ge=1, description="Public diagnostic_report identifier."
    ),
    actor: AuthUser = Depends(require_permission("diagnostic_report", "update")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_diagnostic_report()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a DiagnosticReport resource",
        extra={"event": "route.patch_diagnostic_report", "diagnostic_report_id": diagnostic_report_id},
    )
    log_payload(logger, "diagnostic_report.patch.payload", payload)
    updated = await diagnostic_report_service.patch_diagnostic_report(
        diagnostic_report_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(diagnostic_report_service._to_fhir(updated))


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{diagnostic_report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_diagnostic_report",
    summary="Delete a DiagnosticReport resource",
    description=(
        "Permanently deletes the DiagnosticReport and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "diagnostic_report exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_diagnostic_report(
    diagnostic_report_id: int = Path(
        ..., ge=1, description="Public diagnostic_report identifier."
    ),
    actor: AuthUser = Depends(require_permission("diagnostic_report", "delete")),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
):
    """delete_diagnostic_report() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a DiagnosticReport resource",
        extra={
            "event": "route.delete_diagnostic_report",
            "diagnostic_report_id": diagnostic_report_id,
        },
    )
    await diagnostic_report_service.delete_diagnostic_report(diagnostic_report_id, org_id=actor.org_id)
