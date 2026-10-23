from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.practitioner import get_practitioner_service
from app.schemas.enums import AddressUse, AdministrativeGender
from app.schemas.practitioner import PractitionerCreateSchema, PractitionerPatchSchema
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


# ── Create ───────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_practitioner",
    summary="Create a new Practitioner resource",
    description=(
        "Records a person with a formal responsibility in providing healthcare or "
        "related services. Accepts the full nested payload — identifier, name, telecom, "
        "address, photo, qualification, and communication arrays — atomically in one DB "
        "transaction. Qualification's `issuer` may reference an Organization (e.g. "
        "`'Organization/190001'`) — rejected with 422 if it doesn't exist. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_practitioner(
    payload: PractitionerCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is no longer a request body field at all, and an
    org-less token is rejected outright (403). `user_id`, unlike
    Organization/Location/HealthcareService, is still a plain request body
    field — see PractitionerModel's docstring."""
    logger.info(
        "Create a new Practitioner resource",
        extra={"event": "route.create_practitioner"},
    )
    log_payload(logger, "practitioner.create.payload", payload)
    p = await practitioner_service.create_practitioner(payload, actor.org_id, actor.sub)
    return format_response(
        practitioner_service._to_fhir(p), practitioner_service._to_plain(p), request
    )


# ── Me (must come before /{practitioner_id}) ────────────────────────────


@router.get(
    "/me",
    operation_id="list_my_practitioners",
    summary="List Practitioner resources owned by the authenticated end-user",
    description=(
        "Same filters as `GET /`, always additionally scoped to the authenticated "
        "end-user's own `user_id` (from the gateway-forwarded field at create time), on "
        "top of the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_practitioners(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    active: bool | None = Query(None, description="Filter by active status."),
    gender: AdministrativeGender | None = Query(
        None, description="male|female|other|unknown."
    ),
    family: str | None = Query(None, description="Partial match on family name."),
    given: str | None = Query(None, description="Partial match on any given name."),
    name: str | None = Query(
        None, description="Matches any string field in HumanName."
    ),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    telecom: str | None = Query(None, description="Exact match on any contact value."),
    phone: str | None = Query(
        None, description="Exact match on a phone contact value."
    ),
    email: str | None = Query(
        None, description="Exact match on an email contact value."
    ),
    communication: str | None = Query(
        None, description="Exact match on a communication language code."
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
    params: ListParams = Depends(),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "List Practitioner resources owned by the authenticated end-user",
        extra={"event": "route.list_my_practitioners"},
    )
    rows, total = await practitioner_service.get_me(
        user_id=actor.sub,
        org_id=actor.org_id,
        active=active,
        gender=gender,
        family=family,
        given=given,
        name=name,
        identifier=identifier,
        telecom=telecom,
        phone=phone,
        email=email,
        communication=communication,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        address_use=address_use,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [practitioner_service._to_fhir(p) for p in rows],
        [practitioner_service._to_plain(p) for p in rows],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{practitioner_id}",
    operation_id="get_practitioner_by_id",
    summary="Retrieve a Practitioner resource by public practitioner_id",
    description=(
        "Scoped to the caller's own org — get_practitioner_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
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
    logger.info(
        "Retrieve a Practitioner resource by public practitioner_id",
        extra={
            "event": "route.get_practitioner_by_id",
            "practitioner_id": practitioner_id,
        },
    )
    p = await practitioner_service.get_practitioner_scoped(
        practitioner_id, actor.org_id
    )
    return format_response(
        practitioner_service._to_fhir(p), practitioner_service._to_plain(p), request
    )


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{practitioner_id}",
    operation_id="patch_practitioner",
    summary="Update a Practitioner resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (identifier, name, telecom, address, photo, "
        "qualification, communication — even `[]`) atomically replaces the corresponding "
        "rows; omitted lists are left untouched. "
        "Scoped to the caller's own org — patch_practitioner() raises NotFoundError (404, "
        "not 403 — avoids leaking that a practitioner with this id exists in another org) "
        "if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner(
    payload: PractitionerPatchSchema,
    request: Request,
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_practitioner()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Practitioner resource",
        extra={"event": "route.patch_practitioner", "practitioner_id": practitioner_id},
    )
    log_payload(logger, "practitioner.patch.payload", payload)
    updated = await practitioner_service.patch_practitioner(
        practitioner_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


# ── List ─────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_practitioners",
    summary="List all Practitioner resources",
    description=(
        "Returns a paginated list of Practitioner resources, matching the FHIR R4 "
        "Practitioner search parameter set. Filter by `active`, `gender`, `family` "
        "(partial), `given` (partial), `name` (partial match against any HumanName "
        "sub-field), `identifier` (exact business-identifier value), `telecom`/`phone`/"
        "`email` (exact contact value), `communication` (exact language code), "
        "`address` (partial match across every Address sub-field) or "
        "`address-city`/`address-state`/`address-postalcode`/`address-country`/"
        "`address-use` (one specific sub-field). "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is "
        "not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-practitioner_id`); set `total_mode=none` to skip the "
        "COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_practitioners(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    active: bool | None = Query(None, description="Filter by active status."),
    gender: AdministrativeGender | None = Query(
        None, description="male|female|other|unknown."
    ),
    family: str | None = Query(None, description="Partial match on family name."),
    given: str | None = Query(None, description="Partial match on any given name."),
    name: str | None = Query(
        None, description="Matches any string field in HumanName."
    ),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value."
    ),
    telecom: str | None = Query(None, description="Exact match on any contact value."),
    phone: str | None = Query(
        None, description="Exact match on a phone contact value."
    ),
    email: str | None = Query(
        None, description="Exact match on an email contact value."
    ),
    communication: str | None = Query(
        None, description="Exact match on a communication language code."
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
    rows, total = await practitioner_service.list_practitioners(
        org_id=actor.org_id,
        active=active,
        gender=gender,
        family=family,
        given=given,
        name=name,
        identifier=identifier,
        telecom=telecom,
        phone=phone,
        email=email,
        communication=communication,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        address_use=address_use,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [practitioner_service._to_fhir(p) for p in rows],
        [practitioner_service._to_plain(p) for p in rows],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{practitioner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner",
    summary="Delete a Practitioner resource",
    description=(
        "Permanently deletes the Practitioner and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "practitioner exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_practitioner(
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """delete_practitioner() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org. Delete
    cascades to every sub-resource row."""
    logger.info(
        "Delete a Practitioner resource",
        extra={
            "event": "route.delete_practitioner",
            "practitioner_id": practitioner_id,
        },
    )
    await practitioner_service.delete_practitioner(practitioner_id, org_id=actor.org_id)
