import datetime as dt

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.practitioner_role import get_practitioner_role_service
from app.schemas.practitioner_role import (
    PractitionerRoleCreateSchema,
    PractitionerRolePatchSchema,
)
from app.services.practitioner_role import PractitionerRoleService

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
    operation_id="create_practitioner_role",
    summary="Create a new PractitionerRole resource",
    description=(
        "Records a specific set of roles/locations/specialties/services that a practitioner "
        "may perform at an organization for a period of time. PractitionerRole is set once and "
        "then patched rather than built up incrementally, so this single endpoint accepts "
        "the full nested payload — identifier, code, specialty, location, healthcareService, "
        "telecom, availableTime, notAvailable, and endpoint arrays — atomically in one DB "
        "transaction. Optionally link to a practitioner via `practitioner` (e.g. "
        "`'Practitioner/30001'`) and/or an organization via `organization` (e.g. "
        "`'Organization/190001'`) — both rejected with 422 if they don't exist. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_practitioner_role(
    payload: PractitionerRoleCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner_role", "create")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). PractitionerRole has no
    user_id field at all, like Organization, Location, and HealthcareService."""
    logger.info(
        "Create a new PractitionerRole resource",
        extra={"event": "route.create_practitioner_role"},
    )
    log_payload(logger, "practitioner_role.create.payload", payload)
    pr = await practitioner_role_service.create_practitioner_role(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        practitioner_role_service._to_fhir(pr),
        practitioner_role_service._to_plain(pr),
        request,
    )


@router.get(
    "/{practitioner_role_id}",
    operation_id="get_practitioner_role_by_id",
    summary="Retrieve a PractitionerRole resource by public practitioner_role_id",
    description=(
        "Scoped to the caller's own org — get_practitioner_role_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_practitioner_role(
    request: Request,
    practitioner_role_id: int = Path(
        ..., ge=1, description="Public practitioner_role identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner_role", "read")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    logger.info(
        "Retrieve a PractitionerRole resource by public practitioner_role_id",
        extra={
            "event": "route.get_practitioner_role_by_id",
            "practitioner_role_id": practitioner_role_id,
        },
    )
    pr = await practitioner_role_service.get_practitioner_role_scoped(
        practitioner_role_id, actor.org_id
    )
    return format_response(
        practitioner_role_service._to_fhir(pr),
        practitioner_role_service._to_plain(pr),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{practitioner_role_id}",
    operation_id="patch_practitioner_role",
    summary="Update a PractitionerRole resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every supplied "
        "sub-resource list (identifier, code, specialty, location, healthcareService, telecom, "
        "availableTime, notAvailable, endpoint — even `[]`) atomically replaces the "
        "corresponding rows; omitted lists are left untouched. `practitioner`/`organization` "
        "may be set to null to clear the link — rejected with 422 if the referenced resource "
        "doesn't exist. Scoped to the caller's own org — patch_practitioner_role() raises "
        "NotFoundError (404, not 403 — avoids leaking that a practitioner role with this id "
        "exists in another org) if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner_role(
    payload: PractitionerRolePatchSchema,
    request: Request,
    practitioner_role_id: int = Path(
        ..., ge=1, description="Public practitioner_role identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner_role", "update")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    """updated_by comes from the verified JWT (actor.sub); patch_practitioner_role()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a PractitionerRole resource",
        extra={
            "event": "route.patch_practitioner_role",
            "practitioner_role_id": practitioner_role_id,
        },
    )
    log_payload(logger, "practitioner_role.patch.payload", payload)
    updated = await practitioner_role_service.patch_practitioner_role(
        practitioner_role_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        practitioner_role_service._to_fhir(updated),
        practitioner_role_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_practitioner_roles",
    summary="List all PractitionerRole resources",
    description=(
        "Returns a paginated list of PractitionerRole resources, matching the search "
        "parameter set documented at "
        "https://www.medplum.com/docs/api/fhir/resources/practitionerrole. "
        "Filter by `active`, `identifier` (exact business-identifier value), `role` (exact "
        "code match against `code[]`), `specialty` (exact code match), `email`/`phone` "
        "(exact match against `telecom[]` entries with that system), `telecom` (exact match "
        "against any `telecom[].value` regardless of system), `practitioner`/`organization` "
        "(FHIR reference string to the single flattened reference, e.g. `Practitioner/30001` / "
        "`Organization/190001`), `location`/`service`/`endpoint` (FHIR reference string, e.g. "
        "`Location/230001` / `HealthcareService/150001` / `Endpoint/1`), and `date` (a single "
        "ISO date — matches rows whose `period` contains it, i.e. "
        "`period.start <= date <= period.end`, treating a missing bound as open-ended). "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is "
        "not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-created_at`); set `total_mode=none` to skip the COUNT(*) on "
        "large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_practitioner_roles(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner_role", "read")),
    active: bool | None = Query(None, description="Filter by active status."),
    date: dt.date | None = Query(
        None,
        description="ISO date — matches rows whose period contains it (period.start <= date <= period.end).",
    ),
    email: str | None = Query(
        None, description="Exact match against a telecom entry with system='email'."
    ),
    phone: str | None = Query(
        None, description="Exact match against a telecom entry with system='phone'."
    ),
    telecom: str | None = Query(
        None, description="Exact match against any telecom value, regardless of system."
    ),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    role: str | None = Query(None, description="Exact match on a coded role (code[])."),
    specialty: str | None = Query(None, description="Exact match on a coded specialty."),
    practitioner: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string to the practitioner, e.g. `Practitioner/30001`.",
    ),
    organization: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string to the organization, e.g. `Organization/190001`.",
    ),
    location: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Location/230001`.",
    ),
    service: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `HealthcareService/150001`.",
    ),
    endpoint: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Endpoint/1`.",
    ),
    params: ListParams = Depends(),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_practitioner_roles() raises PermissionDeniedError (403) outright
    for an org-less token."""
    logger.info(
        "List all PractitionerRole resources",
        extra={"event": "route.list_practitioner_roles"},
    )
    items, total = await practitioner_role_service.list_practitioner_roles(
        org_id=actor.org_id,
        active=active,
        date=date,
        email=email,
        phone=phone,
        telecom=telecom,
        identifier=identifier,
        role=role,
        specialty=specialty,
        practitioner=practitioner,
        organization=organization,
        location=location,
        service=service,
        endpoint=endpoint,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [practitioner_role_service._to_fhir(pr) for pr in items],
        [practitioner_role_service._to_plain(pr) for pr in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{practitioner_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_role",
    summary="Delete a PractitionerRole resource",
    description=(
        "Permanently deletes the PractitionerRole and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "practitioner role exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_practitioner_role(
    practitioner_role_id: int = Path(
        ..., ge=1, description="Public practitioner_role identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner_role", "delete")),
    practitioner_role_service: PractitionerRoleService = Depends(
        get_practitioner_role_service
    ),
):
    """delete_practitioner_role() raises NotFoundError (404) if the id
    doesn't exist at all, or if it exists but belongs to a different org.
    Delete cascades to every sub-resource row."""
    logger.info(
        "Delete a PractitionerRole resource",
        extra={
            "event": "route.delete_practitioner_role",
            "practitioner_role_id": practitioner_role_id,
        },
    )
    await practitioner_role_service.delete_practitioner_role(
        practitioner_role_id, org_id=actor.org_id
    )
