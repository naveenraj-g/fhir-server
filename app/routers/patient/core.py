from datetime import date

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.patient import get_patient_service
from app.schemas.enums import AddressUse, AdministrativeGender
from app.schemas.patient import PatientCreateSchema, PatientPatchSchema
from app.services.patient import PatientService

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
    operation_id="create_patient",
    summary="Create a new Patient resource",
    description=(
        "Demographics and other administrative information about an individual "
        "receiving care or other health-related services. Accepts the full nested payload — "
        "identifier, name, telecom, address, photo, contact, communication, general_practitioner, "
        "and link arrays — atomically in one DB transaction. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_patient(
    payload: PatientCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id / actor.sub).
    user_id is forwarded as a request body field representing the patient account owner."""
    logger.info(
        "Create a new Patient resource",
        extra={"event": "route.create_patient"},
    )
    log_payload(logger, "patient.create.payload", payload)
    p = await patient_service.create_patient(payload, actor.org_id, actor.sub)
    return format_response(
        patient_service._to_fhir(p),
        patient_service._to_plain(p),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Me (must come before /{patient_id}) ───────────────────────────────────


@router.get(
    "/me",
    operation_id="list_my_patients",
    summary="List Patient resources owned by the authenticated end-user",
    description=(
        "Same filters as `GET /`, always additionally scoped to the authenticated "
        "end-user's own `user_id` on top of the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_patients(
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "read")),
    active: bool | None = Query(None, description="Filter by active status."),
    gender: AdministrativeGender | None = Query(
        None, description="male|female|other|unknown."
    ),
    birthdate: date | None = Query(
        None, description="Exact match on patient birth date (YYYY-MM-DD)."
    ),
    deceased: bool | None = Query(
        None, description="Filter by deceased status boolean."
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
    general_practitioner: str | None = Query(
        None,
        alias="general-practitioner",
        description="Filter by general practitioner reference or ID.",
    ),
    organization: str | None = Query(
        None,
        description="Filter by managing organization reference or ID.",
    ),
    params: ListParams = Depends(),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "List Patient resources owned by the authenticated end-user",
        extra={"event": "route.list_my_patients"},
    )
    rows, total = await patient_service.get_me(
        user_id=actor.sub,
        org_id=actor.org_id,
        active=active,
        gender=gender,
        birthdate=birthdate,
        deceased=deceased,
        family=family,
        given=given,
        name=name,
        identifier=identifier,
        telecom=telecom,
        phone=phone,
        email=email,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        address_use=address_use,
        general_practitioner=general_practitioner,
        organization=organization,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [patient_service._to_fhir(p) for p in rows],
        [patient_service._to_plain(p) for p in rows],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{patient_id}",
    operation_id="get_patient_by_id",
    summary="Retrieve a Patient resource by public patient_id",
    description=(
        "Scoped to the caller's own org — get_patient_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_patient(
    request: Request,
    patient_id: int = Path(
        ..., ge=1, description="Public patient identifier."
    ),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "Retrieve a Patient resource by public patient_id",
        extra={
            "event": "route.get_patient_by_id",
            "patient_id": patient_id,
        },
    )
    p = await patient_service.get_patient_scoped(patient_id, actor.org_id)
    return format_response(
        patient_service._to_fhir(p), patient_service._to_plain(p), request
    )


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{patient_id}",
    operation_id="patch_patient",
    summary="Update a Patient resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (even `[]`) atomically replaces the corresponding "
        "rows; omitted lists are left untouched. "
        "Scoped to the caller's own org — patch_patient() raises NotFoundError (404, "
        "not 403 — avoids leaking that a patient with this id exists in another org) "
        "if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_patient(
    payload: PatientPatchSchema,
    request: Request,
    patient_id: int = Path(
        ..., ge=1, description="Public patient identifier."
    ),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_patient()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Patient resource",
        extra={"event": "route.patch_patient", "patient_id": patient_id},
    )
    log_payload(logger, "patient.patch.payload", payload)
    updated = await patient_service.patch_patient(
        patient_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        patient_service._to_fhir(updated),
        patient_service._to_plain(updated),
        request,
    )


# ── List ─────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_patients",
    summary="List all Patient resources",
    description=(
        "Returns a paginated list of Patient resources matching search parameters. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_patients(
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "read")),
    active: bool | None = Query(None, description="Filter by active status."),
    gender: AdministrativeGender | None = Query(
        None, description="male|female|other|unknown."
    ),
    birthdate: date | None = Query(
        None, description="Exact match on patient birth date (YYYY-MM-DD)."
    ),
    deceased: bool | None = Query(
        None, description="Filter by deceased status boolean."
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
    general_practitioner: str | None = Query(
        None,
        alias="general-practitioner",
        description="Filter by general practitioner reference or ID.",
    ),
    organization: str | None = Query(
        None,
        description="Filter by managing organization reference or ID.",
    ),
    params: ListParams = Depends(),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "List all Patient resources",
        extra={"event": "route.list_patients"},
    )
    rows, total = await patient_service.list_patients(
        org_id=actor.org_id,
        active=active,
        gender=gender,
        birthdate=birthdate,
        deceased=deceased,
        family=family,
        given=given,
        name=name,
        identifier=identifier,
        telecom=telecom,
        phone=phone,
        email=email,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        address_use=address_use,
        general_practitioner=general_practitioner,
        organization=organization,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [patient_service._to_fhir(p) for p in rows],
        [patient_service._to_plain(p) for p in rows],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient",
    summary="Delete a Patient resource",
    description=(
        "Permanently deletes the Patient and all associated sub-resources. "
        "Scoped to the caller's own org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_patient(
    patient_id: int = Path(
        ..., ge=1, description="Public patient identifier."
    ),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    logger.info(
        "Delete a Patient resource",
        extra={
            "event": "route.delete_patient",
            "patient_id": patient_id,
        },
    )
    await patient_service.delete_patient(patient_id, org_id=actor.org_id)
