from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.practitioner import get_practitioner_service
from app.schemas.enums import AddressUse, AdministrativeGender
from app.schemas.practitioner import (
    PractitionerCreateSchema,
    PractitionerFullCreateSchema,
    PractitionerFullPatchSchema,
    PractitionerPatchSchema,
)
from app.services.practitioner import PractitionerService

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


# ── Create Practitioner ────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_practitioner",
    summary="Create a new Practitioner resource",
    description=(
        "Creates a Practitioner with core demographics (active status, gender, birth date). "
        "The caller's `sub` claim and `activeOrganizationId` from the JWT are automatically bound to the record. "
        "Names, identifiers, telecom, addresses, photos, qualifications, and communications must be added "
        "via the dedicated sub-resource endpoints after creation. " + _CONTENT_NEG
    ),
    response_description="The newly created Practitioner resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_practitioner(
    payload: PractitionerCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """user_id comes straight off the validated payload, but org_id and
    created_by both come from the verified JWT (actor.org_id / actor.sub) —
    org_id is no longer a request body field at all, and an org-less token
    is rejected outright (403)."""
    logger.info(
        "Create a new Practitioner resource",
        extra={"event": "route.create_practitioner"},
    )
    log_payload(logger, "practitioner.create.payload", payload)
    practitioner = await practitioner_service.create_practitioner(
        payload, payload.user_id, actor.org_id, actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(practitioner),
        practitioner_service._to_plain(practitioner),
        request,
    )


@router.post(
    "/full",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_practitioner_full",
    summary="Create a Practitioner resource with all sub-resources in one request",
    description=(
        "Creates a Practitioner and any combination of sub-resources (names, identifiers, telecom, "
        "addresses, photos, qualifications, communications) atomically in a single DB transaction — "
        "if any insert fails the entire request rolls back. "
        "All sub-resource lists are optional; omit any to skip those sub-resources. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_practitioner_full(
    payload: PractitionerFullCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """Same org_id/created_by handling as create_practitioner."""
    logger.info(
        "Create a Practitioner resource with all sub-resources in one request",
        extra={"event": "route.create_practitioner_full"},
    )
    log_payload(logger, "practitioner.create_full.payload", payload)
    practitioner = await practitioner_service.create_practitioner_full(
        payload, payload.user_id, actor.org_id, actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(practitioner),
        practitioner_service._to_plain(practitioner),
        request,
    )


# ── /me — declared before /{practitioner_id} so FastAPI doesn't match "me" as
# a practitioner_id path param ──────────────────────────────────────────────


@router.get(
    "/me",
    operation_id="get_my_practitioner_profile",
    summary="Retrieve the authenticated caller's own Practitioner resource",
    description=(
        "Scoped to the verified JWT's sub + activeOrganizationId — never a client-"
        "suppliable value. Returns the one Practitioner record whose user_id/org_id match "
        "the caller's own token. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_my_practitioner(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """get_me() raises PermissionDeniedError (403) for an org-less token, or
    NotFoundError (404) if no practitioner matches the caller's own user_id/org_id."""
    logger.info(
        "Retrieve the authenticated caller's own Practitioner resource",
        extra={"event": "route.get_my_practitioner_profile"},
    )
    practitioner = await practitioner_service.get_me(actor.sub, actor.org_id)
    return format_response(
        practitioner_service._to_fhir(practitioner),
        practitioner_service._to_plain(practitioner),
        request,
    )


@router.get(
    "/{practitioner_id}",
    operation_id="get_practitioner_by_id",
    summary="Retrieve a Practitioner resource by public practitioner_id",
    description=(
        "Fetches a single Practitioner by its public integer `practitioner_id`. "
        "Access is subject to organization-scoped authorization. " + _CONTENT_NEG
    ),
    response_description="The requested Practitioner resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_practitioner(
    request: Request,
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """Fetches the practitioner scoped to the caller's org —
    get_practitioner_scoped() raises PermissionDeniedError (403) outright
    for an org-less token, or NotFoundError (404, never 403) if it belongs
    to a different org, so existence isn't leaked."""
    logger.info(
        "Retrieve a Practitioner resource by public practitioner_id",
        extra={"event": "route.get_practitioner_by_id", "practitioner_id": practitioner_id},
    )
    practitioner = await practitioner_service.get_practitioner_scoped(
        practitioner_id, actor.org_id
    )
    return format_response(
        practitioner_service._to_fhir(practitioner),
        practitioner_service._to_plain(practitioner),
        request,
    )


# ── Patch Practitioner ─────────────────────────────────────────────────────


@router.patch(
    "/{practitioner_id}",
    operation_id="patch_practitioner",
    summary="Partially update a Practitioner resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. "
        "Patchable fields: active, gender, birth_date. "
        "To modify names, identifiers, telecom, addresses, photos, qualifications, or communications, "
        "use the dedicated sub-resource endpoints. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner(
    payload: PractitionerPatchSchema,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_practitioner()
    raises NotFoundError (404, not 403 — avoids leaking that a practitioner
    with this id exists in another org) if actor.org_id doesn't match."""
    logger.info(
        "Partially update a Practitioner resource",
        extra={"event": "route.patch_practitioner", "practitioner_id": practitioner_id},
    )
    log_payload(logger, "practitioner.patch.payload", payload)
    updated = await practitioner_service.patch_practitioner(
        practitioner_id, payload, actor.sub, actor.org_id
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


@router.patch(
    "/{practitioner_id}/full",
    operation_id="patch_practitioner_full",
    summary="Atomically update a Practitioner and replace any sub-resource lists in one request",
    description=(
        "Patches a Practitioner's scalar fields (same semantics as `PATCH /{practitioner_id}`) AND "
        "replaces sub-resource lists atomically in a single DB transaction. "
        "For each list that is **provided** (even `[]`): all existing rows are deleted and the "
        "new items are inserted. Lists that are **omitted** (null / not in body) are left untouched. "
        "Qualifications with nested identifiers are handled correctly. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner_full(
    payload: PractitionerFullPatchSchema,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """Same actor-derived updated_by and org_id ownership gate as
    patch_practitioner — patch_practitioner_full() raises NotFoundError (404) on mismatch."""
    logger.info(
        "Atomically update a Practitioner and replace any sub-resource lists in one request",
        extra={"event": "route.patch_practitioner_full", "practitioner_id": practitioner_id},
    )
    log_payload(logger, "practitioner.patch_full.payload", payload)
    updated = await practitioner_service.patch_practitioner_full(
        practitioner_id, payload, actor.sub, actor.org_id
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


# ── List Practitioners ─────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_practitioners",
    summary="List all Practitioner resources",
    description=(
        "Returns a paginated list of Practitioner resources, matching the FHIR R4 "
        "Practitioner search parameter set (mirroring Medplum's documented filters). "
        "Filter by `family`/`given` (partial match on one HumanName sub-field) or `name` "
        "(partial match across family/given/prefix/suffix/text combined), `identifier` "
        "(exact business-identifier value, e.g. NPI), `gender`, `active`, "
        "`address` (partial match across every Address sub-field) or "
        "`address-city`/`address-state`/`address-postalcode`/`address-country`/`address-use` "
        "(one specific sub-field), `telecom` (any system) or `email`/`phone` (one system), "
        "`communication` (Practitioner.communication.language code), "
        "`qualification-code` (exact match on a qualification's coded type), or `user_id`. "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is "
        "not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-birth_date`); set `total_mode=none` to skip the COUNT(*) "
        "on large result sets. " + _CONTENT_NEG
    ),
    response_description="Paginated Practitioner resources",
    responses={**_LIST_200},
)
async def list_practitioners(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    family: str | None = Query(
        None, description="Filter by family (last) name — partial match."
    ),
    given: str | None = Query(
        None, description="Filter by given name — partial match."
    ),
    name: str | None = Query(
        None,
        description="Partial match against any HumanName sub-field (family, given, prefix, suffix, text).",
    ),
    gender: AdministrativeGender | None = Query(
        None, description="male|female|other|unknown"
    ),
    active: bool | None = Query(None, description="Filter by active status."),
    user_id: str | None = Query(None, description="Filter by user_id (JWT sub claim)."),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value (e.g. NPI)."
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
    telecom: str | None = Query(
        None,
        description="Filter by any telecom value, regardless of system — partial match.",
    ),
    email: str | None = Query(
        None, description="Filter by telecom email — partial match, system=email only."
    ),
    phone: str | None = Query(
        None, description="Filter by telecom phone — partial match, system=phone only."
    ),
    communication: str | None = Query(
        None,
        description="Exact match on Practitioner.communication.language code (e.g. en, fr).",
    ),
    qualification_code: str | None = Query(
        None,
        alias="qualification-code",
        description="Exact match on a qualification's coded type (e.g. MD, RN).",
    ),
    params: ListParams = Depends(),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_practitioners() raises PermissionDeniedError (403) outright for an
    org-less token."""
    logger.info(
        "List all Practitioner resources",
        extra={"event": "route.list_practitioners"},
    )
    practitioners, total = await practitioner_service.list_practitioners(
        user_id=user_id,
        org_id=actor.org_id,
        family=family,
        given=given,
        name=name,
        gender=gender,
        active=active,
        identifier=identifier,
        communication=communication,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        address_use=address_use,
        telecom=telecom,
        email=email,
        phone=phone,
        qualification_code=qualification_code,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [practitioner_service._to_fhir(p) for p in practitioners],
        [practitioner_service._to_plain(p) for p in practitioners],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete Practitioner ────────────────────────────────────────────────────


@router.delete(
    "/{practitioner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner",
    summary="Delete a Practitioner resource",
    description=(
        "Permanently deletes the Practitioner and all associated sub-resources "
        "(names, identifiers, telecom, addresses, photos, qualifications, communications). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_practitioner(
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """delete_practitioner() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org. Delete
    cascades to every sub-resource row."""
    logger.info(
        "Delete a Practitioner resource",
        extra={"event": "route.delete_practitioner", "practitioner_id": practitioner_id},
    )
    await practitioner_service.delete_practitioner(
        practitioner_id, actor.org_id
    )
