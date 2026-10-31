from datetime import date

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.related_person import get_related_person_service
from app.schemas.related_person import (
    RelatedPersonCreateSchema,
    RelatedPersonPatchSchema,
)
from app.services.related_person import RelatedPersonService

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


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_related_person",
    summary="Create a new RelatedPerson resource",
    description=(
        "A person that is related to a patient, but who is not a direct target of care. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) "
        "— an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_related_person(
    payload: RelatedPersonCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("related_person", "create")),
    related_person_service: RelatedPersonService = Depends(
        get_related_person_service
    ),
):
    logger.info(
        "Create a new RelatedPerson resource",
        extra={"event": "route.create_related_person"},
    )
    log_payload(logger, "related_person.create.payload", payload)
    model = await related_person_service.create_related_person(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        related_person_service._to_fhir(model),
        related_person_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{related_person_id}",
    operation_id="get_related_person",
    summary="Get a RelatedPerson resource by ID",
    description=(
        "Returns the full RelatedPerson resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_related_person(
    request: Request,
    related_person_id: int = Path(
        ..., ge=1, description="Public RelatedPerson identifier."
    ),
    actor: AuthUser = Depends(require_permission("related_person", "read")),
    related_person_service: RelatedPersonService = Depends(
        get_related_person_service
    ),
):
    logger.info(
        "Get a RelatedPerson resource by ID",
        extra={
            "event": "route.get_related_person",
            "related_person_id": related_person_id,
        },
    )
    model = await related_person_service.get_related_person_scoped(
        related_person_id, actor.org_id
    )
    return format_response(
        related_person_service._to_fhir(model),
        related_person_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{related_person_id}",
    operation_id="patch_related_person",
    summary="Update a RelatedPerson resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_related_person(
    payload: RelatedPersonPatchSchema,
    request: Request,
    related_person_id: int = Path(
        ..., ge=1, description="Public RelatedPerson identifier."
    ),
    actor: AuthUser = Depends(require_permission("related_person", "update")),
    related_person_service: RelatedPersonService = Depends(
        get_related_person_service
    ),
):
    logger.info(
        "Update a RelatedPerson resource",
        extra={
            "event": "route.patch_related_person",
            "related_person_id": related_person_id,
        },
    )
    log_payload(logger, "related_person.patch.payload", payload)
    updated = await related_person_service.patch_related_person(
        related_person_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        related_person_service._to_fhir(updated),
        related_person_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_related_persons",
    summary="List all RelatedPerson resources",
    description=(
        "Returns a paginated list of RelatedPerson resources. Filter by active, "
        "patient, relationship, name, telecom, gender, birth-date, address, "
        "identifier, email, phone. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_related_persons(
    request: Request,
    actor: AuthUser = Depends(require_permission("related_person", "read")),
    active: bool | None = Query(
        None, description="Whether the related person record is in active use."
    ),
    patient: str | None = Query(
        None, description="Patient reference or public ID."
    ),
    relationship: str | None = Query(
        None, description="Relationship type text or coding."
    ),
    name: str | None = Query(
        None, description="A portion of any name of the related person."
    ),
    telecom: str | None = Query(
        None, description="The value in any kind of telecom detail."
    ),
    gender: str | None = Query(
        None, description="Gender of the related person (male|female|other|unknown)."
    ),
    birth_date: date | None = Query(
        None, description="The date on which the related person was born (YYYY-MM-DD)."
    ),
    address: str | None = Query(
        None, description="A server defined search that may match any of the string fields in Address."
    ),
    address_city: str | None = Query(
        None, description="A city specified in an address."
    ),
    address_state: str | None = Query(
        None, description="A state specified in an address."
    ),
    address_postal_code: str | None = Query(
        None, description="A postal code specified in an address."
    ),
    address_country: str | None = Query(
        None, description="A country specified in an address."
    ),
    identifier: str | None = Query(
        None, description="An identifier for the related person."
    ),
    email: str | None = Query(
        None, description="A value in an email contact."
    ),
    phone: str | None = Query(
        None, description="A value in a phone contact."
    ),
    pagination: ListParams = Depends(),
    related_person_service: RelatedPersonService = Depends(
        get_related_person_service
    ),
):
    total, rows = await related_person_service.list_related_persons(
        org_id=actor.org_id,
        active=active,
        patient=patient,
        relationship=relationship,
        name=name,
        telecom=telecom,
        gender=gender,
        birth_date=birth_date,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        identifier=identifier,
        email=email,
        phone=phone,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=pagination.sort,
    )
    return format_paginated_response(
        [related_person_service._to_fhir(r) for r in rows],
        [related_person_service._to_plain(r) for r in rows],
        total,
        pagination.limit,
        pagination.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{related_person_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_related_person",
    summary="Delete a RelatedPerson resource",
    description=(
        "Permanently deletes a RelatedPerson resource and all nested child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={
        204: {"description": "RelatedPerson deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_related_person(
    related_person_id: int = Path(
        ..., ge=1, description="Public RelatedPerson identifier."
    ),
    actor: AuthUser = Depends(require_permission("related_person", "delete")),
    related_person_service: RelatedPersonService = Depends(
        get_related_person_service
    ),
):
    logger.info(
        "Delete a RelatedPerson resource",
        extra={
            "event": "route.delete_related_person",
            "related_person_id": related_person_id,
        },
    )
    await related_person_service.delete_related_person(
        related_person_id, org_id=actor.org_id
    )
