from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.healthcare_service import get_healthcare_service_service
from app.schemas.healthcare_service import (
    HealthcareServiceCreateSchema,
    HealthcareServicePatchSchema,
)
from app.services.healthcare_service import HealthcareServiceService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
)

router = APIRouter()

logger = get_logger(__name__)

_FHIR_REFERENCE_PATTERN = r"^[A-Za-z]+/[0-9]+$"


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_healthcare_service",
    summary="Create a new HealthcareService resource",
    description=(
        "Records the details of a healthcare service available at a location, or by an "
        "organization, for a certain type of patient. HealthcareService is set once and "
        "then patched rather than built up incrementally, so this single endpoint accepts "
        "the full nested payload — identifier, category, type, specialty, location, telecom, "
        "coverageArea, serviceProvisionCode, eligibility, program, characteristic, "
        "communication, referralMethod, availableTime, notAvailable, and endpoint arrays — "
        "atomically in one DB transaction. Optionally link to a providing organization via "
        "`provided_by` (e.g. `'Organization/190001'`) — rejected with 422 if it doesn't exist. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_healthcare_service(
    payload: HealthcareServiceCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("healthcare_service", "create")),
    healthcare_service_service: HealthcareServiceService = Depends(
        get_healthcare_service_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). HealthcareService has no
    user_id field at all, like Organization and Location."""
    logger.info(
        "Create a new HealthcareService resource",
        extra={"event": "route.create_healthcare_service"},
    )
    log_payload(logger, "healthcare_service.create.payload", payload)
    hs = await healthcare_service_service.create_healthcare_service(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        healthcare_service_service._to_fhir(hs),
        healthcare_service_service._to_plain(hs),
        request,
    )


@router.get(
    "/{healthcare_service_id}",
    operation_id="get_healthcare_service_by_id",
    summary="Retrieve a HealthcareService resource by public healthcare_service_id",
    description=(
        "Scoped to the caller's own org — get_healthcare_service_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_healthcare_service(
    request: Request,
    healthcare_service_id: int = Path(
        ..., ge=1, description="Public healthcare_service identifier."
    ),
    actor: AuthUser = Depends(require_permission("healthcare_service", "read")),
    healthcare_service_service: HealthcareServiceService = Depends(
        get_healthcare_service_service
    ),
):
    logger.info(
        "Retrieve a HealthcareService resource by public healthcare_service_id",
        extra={
            "event": "route.get_healthcare_service_by_id",
            "healthcare_service_id": healthcare_service_id,
        },
    )
    hs = await healthcare_service_service.get_healthcare_service_scoped(
        healthcare_service_id, actor.org_id
    )
    return format_response(
        healthcare_service_service._to_fhir(hs),
        healthcare_service_service._to_plain(hs),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{healthcare_service_id}",
    operation_id="patch_healthcare_service",
    summary="Update a HealthcareService resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every supplied "
        "sub-resource list (identifier, category, type, specialty, location, telecom, "
        "coverageArea, serviceProvisionCode, eligibility, program, characteristic, "
        "communication, referralMethod, availableTime, notAvailable, endpoint — even `[]`) "
        "atomically replaces the corresponding rows; omitted lists are left untouched. "
        "`provided_by` may be set to null to clear the providing-organization link — rejected "
        "with 422 if the referenced organization doesn't exist. "
        "Scoped to the caller's own org — patch_healthcare_service() raises NotFoundError "
        "(404, not 403 — avoids leaking that a healthcare service with this id exists in "
        "another org) if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_healthcare_service(
    payload: HealthcareServicePatchSchema,
    request: Request,
    healthcare_service_id: int = Path(
        ..., ge=1, description="Public healthcare_service identifier."
    ),
    actor: AuthUser = Depends(require_permission("healthcare_service", "update")),
    healthcare_service_service: HealthcareServiceService = Depends(
        get_healthcare_service_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_healthcare_service()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a HealthcareService resource",
        extra={
            "event": "route.patch_healthcare_service",
            "healthcare_service_id": healthcare_service_id,
        },
    )
    log_payload(logger, "healthcare_service.patch.payload", payload)
    updated = await healthcare_service_service.patch_healthcare_service(
        healthcare_service_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        healthcare_service_service._to_fhir(updated),
        healthcare_service_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_healthcare_services",
    summary="List all HealthcareService resources",
    description=(
        "Returns a paginated list of HealthcareService resources, matching the search "
        "parameter set documented at "
        "https://www.medplum.com/docs/api/fhir/resources/healthcareservice. "
        "Filter by `name` (partial match), `identifier` (exact business-identifier value), "
        "`active`, `service-category`/`service-type`/`specialty`/`characteristic`/`program` "
        "(exact code match), `organization` (FHIR reference string to the providing "
        "Organization), `location`/`coverage-area`/`endpoint` (FHIR reference string, e.g. "
        "`Location/230001` / `Endpoint/1`). Medplum's `offered-in` search parameter has no "
        "equivalent here — `HealthcareService.offeredIn` doesn't exist in FHIR R4 (it's an "
        "R4B/R5 addition), and this server targets R4 only. "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is "
        "not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-name`); set `total_mode=none` to skip the COUNT(*) on large "
        "result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_healthcare_services(
    request: Request,
    actor: AuthUser = Depends(require_permission("healthcare_service", "read")),
    active: bool | None = Query(None, description="Filter by active status."),
    name: str | None = Query(
        None, description="Partial match against the service name."
    ),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    category: str | None = Query(
        None,
        alias="service-category",
        description="Exact match on a coded service category.",
    ),
    service_type: str | None = Query(
        None,
        alias="service-type",
        description="Exact match on a coded service type.",
    ),
    specialty: str | None = Query(
        None, description="Exact match on a coded specialty."
    ),
    characteristic: str | None = Query(
        None, description="Exact match on a coded service characteristic."
    ),
    program: str | None = Query(
        None, description="Exact match on a coded program supported by this service."
    ),
    provided_by: str | None = Query(
        None,
        alias="organization",
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string to the providing Organization, e.g. `Organization/190001`.",
    ),
    location: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Location/230001`.",
    ),
    coverage_area: str | None = Query(
        None,
        alias="coverage-area",
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Location/230001`.",
    ),
    endpoint: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Endpoint/1`.",
    ),
    params: ListParams = Depends(),
    healthcare_service_service: HealthcareServiceService = Depends(
        get_healthcare_service_service
    ),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_healthcare_services() raises PermissionDeniedError (403) outright
    for an org-less token."""
    logger.info(
        "List all HealthcareService resources",
        extra={"event": "route.list_healthcare_services"},
    )
    items, total = await healthcare_service_service.list_healthcare_services(
        org_id=actor.org_id,
        active=active,
        name=name,
        identifier=identifier,
        category=category,
        service_type=service_type,
        specialty=specialty,
        characteristic=characteristic,
        program=program,
        provided_by=provided_by,
        location=location,
        coverage_area=coverage_area,
        endpoint=endpoint,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [healthcare_service_service._to_fhir(hs) for hs in items],
        [healthcare_service_service._to_plain(hs) for hs in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{healthcare_service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_healthcare_service",
    summary="Delete a HealthcareService resource",
    description=(
        "Permanently deletes the HealthcareService and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "healthcare service exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_healthcare_service(
    healthcare_service_id: int = Path(
        ..., ge=1, description="Public healthcare_service identifier."
    ),
    actor: AuthUser = Depends(require_permission("healthcare_service", "delete")),
    healthcare_service_service: HealthcareServiceService = Depends(
        get_healthcare_service_service
    ),
):
    """delete_healthcare_service() raises NotFoundError (404) if the id
    doesn't exist at all, or if it exists but belongs to a different org.
    Delete cascades to every sub-resource row."""
    logger.info(
        "Delete a HealthcareService resource",
        extra={
            "event": "route.delete_healthcare_service",
            "healthcare_service_id": healthcare_service_id,
        },
    )
    await healthcare_service_service.delete_healthcare_service(
        healthcare_service_id, org_id=actor.org_id
    )
