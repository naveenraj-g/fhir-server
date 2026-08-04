from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.pagination import ListParams
from app.di.dependencies.organization import get_organization_service
from app.schemas.enums import AddressUse
from app.schemas.organization import OrganizationCreateSchema, OrganizationPatchSchema
from app.services.organization import OrganizationService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
)

router = APIRouter()

_FHIR_REFERENCE_PATTERN = r"^[A-Za-z]+/[0-9]+$"


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_organization",
    summary="Create a new Organization resource",
    description=(
        "Records a formally or informally recognized grouping of people or organizations "
        "formed for the purpose of achieving some form of collective action. "
        "Organization is set once at onboarding rather than built up incrementally, so this "
        "single endpoint accepts the full nested payload — identifier, type, alias, telecom, "
        "address, contact, and endpoint arrays — atomically in one DB transaction. "
        "Optionally link to a parent organization via `partof` (e.g. `'Organization/190001'`) — "
        "rejected with 422 if the referenced organization doesn't exist. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_organization(
    payload: OrganizationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("organization", "create")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). Organization has no user_id
    field at all, unlike every other resource."""
    org = await organization_service.create_organization(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        organization_service._to_fhir(org), organization_service._to_plain(org), request
    )


@router.get(
    "/{organization_id}",
    operation_id="get_organization_by_id",
    summary="Retrieve an Organization resource by public organization_id",
    description=(
        "Scoped to the caller's own org — get_organization_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_organization(
    request: Request,
    organization_id: int = Path(
        ..., ge=1, description="Public organization identifier."
    ),
    actor: AuthUser = Depends(require_permission("organization", "read")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    org = await organization_service.get_organization_scoped(
        organization_id, actor.org_id
    )
    return format_response(
        organization_service._to_fhir(org), organization_service._to_plain(org), request
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{organization_id}",
    operation_id="patch_organization",
    summary="Update an Organization resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every supplied "
        "sub-resource list (identifier, type, alias, telecom, address, contact, endpoint — even "
        "`[]`) atomically replaces the corresponding rows; omitted lists are left untouched. "
        "`partof` may be set to null to clear the parent link — rejected with 422 if the "
        "referenced organization doesn't exist or setting it would create a circular hierarchy. "
        "Scoped to the caller's own org — patch_organization() raises NotFoundError (404, not "
        "403 — avoids leaking that an organization with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_organization(
    payload: OrganizationPatchSchema,
    request: Request,
    organization_id: int = Path(..., ge=1, description="Public organization identifier."),
    actor: AuthUser = Depends(require_permission("organization", "update")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_organization()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    updated = await organization_service.patch_organization(
        organization_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        organization_service._to_fhir(updated),
        organization_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_organizations",
    summary="List all Organization resources",
    description=(
        "Returns a paginated list of Organization resources, matching the FHIR R4 Organization "
        "search parameter set (mirroring Medplum's documented filters). "
        "Filter by `name` (partial match against name or any alias), `identifier` (exact "
        "business-identifier value), `type` (exact code match), `active`, "
        "`address` (partial match across every Address sub-field) or "
        "`address-city`/`address-state`/`address-postalcode`/`address-country`/`address-use` "
        "(one specific sub-field), `partof`/`endpoint` (FHIR reference string, e.g. "
        "`Organization/190001` / `Endpoint/1`). "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is "
        "not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-name`); set `total_mode=none` to skip the COUNT(*) on large "
        "result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_organizations(
    request: Request,
    actor: AuthUser = Depends(require_permission("organization", "read")),
    active: bool | None = Query(None, description="Filter by active status."),
    name: str | None = Query(
        None, description="Partial match against organization name or any alias."
    ),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    org_type: str | None = Query(
        None, alias="type", description="Exact match on a coded organization type."
    ),
    address: str | None = Query(
        None,
        description="Partial match against any Address sub-field (line, city, district, state, country, postalCode, text).",
    ),
    address_city: str | None = Query(
        None,
        alias="address-city",
        description="Filter by address city — partial match.",
    ),
    address_state: str | None = Query(
        None,
        alias="address-state",
        description="Filter by address state — partial match.",
    ),
    address_postal_code: str | None = Query(
        None,
        alias="address-postalcode",
        description="Filter by address postal code — exact match.",
    ),
    address_country: str | None = Query(
        None,
        alias="address-country",
        description="Filter by address country — partial match.",
    ),
    address_use: AddressUse | None = Query(
        None, alias="address-use", description="home|work|temp|old|billing."
    ),
    partof: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Organization/190001`.",
    ),
    endpoint: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Endpoint/1`.",
    ),
    params: ListParams = Depends(),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_organizations() raises PermissionDeniedError (403) outright for an
    org-less token."""
    orgs, total = await organization_service.list_organizations(
        org_id=actor.org_id,
        active=active,
        name=name,
        identifier=identifier,
        org_type=org_type,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        address_use=address_use,
        partof=partof,
        endpoint=endpoint,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [organization_service._to_fhir(o) for o in orgs],
        [organization_service._to_plain(o) for o in orgs],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_organization",
    summary="Delete an Organization resource",
    description=(
        "Permanently deletes the Organization and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "organization exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_organization(
    organization_id: int = Path(..., ge=1, description="Public organization identifier."),
    actor: AuthUser = Depends(require_permission("organization", "delete")),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """delete_organization() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org. Delete
    cascades to every sub-resource row."""
    await organization_service.delete_organization(
        organization_id, org_id=actor.org_id
    )
