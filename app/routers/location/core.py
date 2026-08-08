from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.location import get_location_service
from app.models.location.enums import LocationStatus
from app.schemas.enums import AddressUse
from app.schemas.location import LocationCreateSchema, LocationPatchSchema
from app.services.location import LocationService

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
    operation_id="create_location",
    summary="Create a new Location resource",
    description=(
        "Records a physical place where services are provided, or resources and "
        "participants may be stored, found, contained or accommodated. "
        "A Location is registered once rather than built up incrementally, so this single "
        "endpoint accepts the full nested payload — identifier, type, alias, telecom, "
        "hoursOfOperation and endpoint arrays — atomically in one DB transaction. "
        "`address` is 0..1 in FHIR R4 (unlike Organization's repeating address), so it is "
        "supplied as flat `address_*` fields rather than a list. "
        "Optionally link to a containing location via `part_of` (e.g. `'Location/230001'`) "
        "or an owning organization via `managing_organization` (e.g. `'Organization/190001'`) "
        "— either is rejected with 422 if the referenced resource doesn't exist in the "
        "caller's org. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_location(
    payload: LocationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("location", "create")),
    location_service: LocationService = Depends(get_location_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403). Location has no user_id field at all,
    same as Organization."""
    logger.info(
        "Create a new Location resource",
        extra={"event": "route.create_location"},
    )
    log_payload(logger, "location.create.payload", payload)
    loc = await location_service.create_location(payload, actor.org_id, actor.sub)
    return format_response(
        location_service._to_fhir(loc), location_service._to_plain(loc), request
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{location_id}",
    operation_id="get_location_by_id",
    summary="Retrieve a Location resource by public location_id",
    description=(
        "Scoped to the caller's own org — get_location_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_location(
    request: Request,
    location_id: int = Path(..., ge=1, description="Public location identifier."),
    actor: AuthUser = Depends(require_permission("location", "read")),
    location_service: LocationService = Depends(get_location_service),
):
    logger.info(
        "Retrieve a Location resource by public location_id",
        extra={"event": "route.get_location_by_id", "location_id": location_id},
    )
    loc = await location_service.get_location_scoped(location_id, actor.org_id)
    return format_response(
        location_service._to_fhir(loc), location_service._to_plain(loc), request
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{location_id}",
    operation_id="patch_location",
    summary="Update a Location resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every supplied "
        "sub-resource list (identifier, type, alias, telecom, hoursOfOperation, endpoint — even "
        "`[]`) atomically replaces the corresponding rows; omitted lists are left untouched. "
        "`part_of` and `managing_organization` may each be set to null to clear the link — "
        "rejected with 422 if the referenced resource doesn't exist, or if setting `part_of` "
        "would create a circular location hierarchy (A contained in B contained in A). "
        "Scoped to the caller's own org — patch_location() raises NotFoundError (404, not 403 "
        "— avoids leaking that a location with this id exists in another org) if actor.org_id "
        "doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_location(
    payload: LocationPatchSchema,
    request: Request,
    location_id: int = Path(..., ge=1, description="Public location identifier."),
    actor: AuthUser = Depends(require_permission("location", "update")),
    location_service: LocationService = Depends(get_location_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_location()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Location resource",
        extra={"event": "route.patch_location", "location_id": location_id},
    )
    log_payload(logger, "location.patch.payload", payload)
    updated = await location_service.patch_location(
        location_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        location_service._to_fhir(updated),
        location_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_locations",
    summary="List all Location resources",
    description=(
        "Returns a paginated list of Location resources, matching the FHIR R4 Location "
        "search parameter set (mirroring Medplum's documented filters). "
        "Filter by `name` (partial match against the location's name or any alias), "
        "`identifier` (exact business-identifier value), `status`, `operational-status`, "
        "`type` and `physical-type` (exact code match), "
        "`address` (partial match across every Address sub-field) or "
        "`address-city`/`address-state`/`address-postalcode`/`address-country`/`address-use` "
        "(one specific sub-field), `organization`/`partof`/`endpoint` (FHIR reference string, "
        "e.g. `Organization/190001` / `Location/230001` / `Endpoint/1`), and `near` "
        "(`[latitude]|[longitude]|[distance]|[units]`, great-circle radius search against "
        "Location.position). "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is not a "
        "client-suppliable filter. "
        "Sort with `sort` (e.g. `-name`); set `total_mode=none` to skip the COUNT(*) on large "
        "result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_locations(
    request: Request,
    actor: AuthUser = Depends(require_permission("location", "read")),
    name: str | None = Query(
        None, description="Partial match against the location name or any alias."
    ),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    location_status: LocationStatus | None = Query(
        None, alias="status", description="active|suspended|inactive."
    ),
    operational_status: str | None = Query(
        None,
        alias="operational-status",
        description="Exact match on the operational status code (e.g. `U` for Unoccupied).",
    ),
    location_type: str | None = Query(
        None,
        alias="type",
        description="Exact match on a coded function performed at the location (e.g. `HOSP`).",
    ),
    physical_type: str | None = Query(
        None,
        alias="physical-type",
        description="Exact match on the physical form code (e.g. `wi` for Wing, `ro` for Room).",
    ),
    address: str | None = Query(
        None,
        description="Partial match against any Address sub-field (line, city, district, state, country, postalCode, text).",
    ),
    address_city: str | None = Query(
        None, alias="address-city", description="Filter by address city — partial match."
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
    organization: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="Managing organization, as a FHIR reference string, e.g. `Organization/190001`.",
    ),
    partof: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="Containing location, as a FHIR reference string, e.g. `Location/230001`.",
    ),
    endpoint: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Endpoint/1`.",
    ),
    near: str | None = Query(
        None,
        description=(
            "Radius search against Location.position, as "
            "`[latitude]|[longitude]|[distance]|[units]` — e.g. "
            "`42.25475478|-83.6945691|11.20|km`. Units default to km; km, m and mi are "
            "accepted. Locations with no recorded position never match."
        ),
    ),
    params: ListParams = Depends(),
    location_service: LocationService = Depends(get_location_service),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_locations() raises PermissionDeniedError (403) outright for an
    org-less token."""
    logger.info(
        "List all Location resources",
        extra={"event": "route.list_locations"},
    )
    locations, total = await location_service.list_locations(
        org_id=actor.org_id,
        name=name,
        identifier=identifier,
        location_status=location_status,
        operational_status=operational_status,
        location_type=location_type,
        physical_type=physical_type,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        address_use=address_use,
        organization=organization,
        partof=partof,
        endpoint=endpoint,
        near=near,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [location_service._to_fhir(loc) for loc in locations],
        [location_service._to_plain(loc) for loc in locations],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_location",
    summary="Delete a Location resource",
    description=(
        "Permanently deletes the Location and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "location exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_location(
    location_id: int = Path(..., ge=1, description="Public location identifier."),
    actor: AuthUser = Depends(require_permission("location", "delete")),
    location_service: LocationService = Depends(get_location_service),
):
    """delete_location() raises NotFoundError (404) if the id doesn't exist at
    all, or if it exists but belongs to a different org. Delete cascades to
    every sub-resource row."""
    logger.info(
        "Delete a Location resource",
        extra={"event": "route.delete_location", "location_id": location_id},
    )
    await location_service.delete_location(location_id, org_id=actor.org_id)
