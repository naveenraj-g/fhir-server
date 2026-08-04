from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.pagination import ListParams
from app.di.dependencies.patient import get_patient_service
from app.models.patient.enums import AddressUse, PatientGender
from app.schemas.patient import (
    PatientCreateSchema,
    PatientFullCreateSchema,
    PatientFullPatchSchema,
    PatientPatchSchema,
)
from app.services.patient import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _FHIR_REFERENCE_PATTERN,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
    _SINGLE_CORE_200,
    _FhirDateItem,
)

router = APIRouter()


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_patient",
    summary="Create a new Patient resource",
    description=(
        "Creates a Patient with core demographic scalar fields (gender, birth date, active status, "
        "marital status, deceased, managing organization). "
        "Names, identifiers, telecom, addresses, photos, contacts, communications, "
        "general practitioners, and links must be added via the dedicated sub-resource endpoints. "
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
    """Create a Patient from core scalar fields; user_id comes straight off
    the validated payload, but org_id and created_by both come from the
    verified JWT (actor.org_id / actor.sub) — org_id is no longer a request
    body field at all, and an org-less token is rejected outright (403)."""
    patient = await patient_service.create_patient(
        payload, payload.user_id, actor.org_id, actor.sub
    )
    return format_response(
        patient_service._to_fhir(patient), patient_service._to_plain(patient), request
    )


@router.post(
    "/full",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_patient_full",
    summary="Create a Patient resource with all sub-resources in one request",
    description=(
        "Creates a Patient and any combination of sub-resources (names, identifiers, telecom, "
        "addresses, photos, contacts, communications, general practitioners, links) atomically "
        "in a single DB transaction — if any insert fails the entire request rolls back. "
        "All sub-resource lists are optional; omit any to skip those sub-resources. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_patient_full(
    payload: PatientFullCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Create a Patient plus any supplied sub-resource lists, atomically.
    Same org_id/created_by handling as create_patient."""
    patient = await patient_service.create_patient_full(
        payload, payload.user_id, actor.org_id, actor.sub
    )
    return format_response(
        patient_service._to_fhir(patient), patient_service._to_plain(patient), request
    )


# ── /me — declared before /{patient_id} so FastAPI doesn't match "me" as a
# patient_id path param ──────────────────────────────────────────────────────


@router.get(
    "/me",
    operation_id="get_my_patient_record",
    summary="Retrieve the authenticated caller's own Patient resource",
    description=(
        "Scoped to the verified JWT's sub + activeOrganizationId — never a client-"
        "suppliable value. Returns the one Patient record whose user_id/org_id match "
        "the caller's own token. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_my_patient(
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """get_me() raises PermissionDeniedError (403) for an org-less token, or
    NotFoundError (404) if no patient matches the caller's own user_id/org_id."""
    patient = await patient_service.get_me(actor.sub, actor.org_id)
    return format_response(
        patient_service._to_fhir(patient), patient_service._to_plain(patient), request
    )


@router.get(
    "/{patient_id}",
    operation_id="get_patient_by_id",
    summary="Retrieve a Patient resource by public patient_id",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_patient(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Fetches the patient scoped to the caller's org — get_patient_scoped()
    raises PermissionDeniedError (403) outright for an org-less token, or
    NotFoundError (404, never 403) if it belongs to a different org, so
    existence isn't leaked."""
    patient = await patient_service.get_patient_scoped(patient_id, actor.org_id)
    return format_response(
        patient_service._to_fhir(patient), patient_service._to_plain(patient), request
    )


@router.get(
    "/{patient_id}/core",
    operation_id="get_patient_core_by_id",
    summary="Retrieve only a Patient's own table data — no sub-resources",
    description=(
        "Returns just the Patient resource's scalar fields (demographics, marital status, "
        "deceased, multiple birth, managing organization) with none of the nine sub-resource "
        "arrays (name, identifier, telecom, address, photo, contact, communication, "
        "generalPractitioner, link) attached. One query against the patients table only — "
        "use this instead of `GET /{patient_id}` when the sub-resource arrays aren't needed. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_CORE_200, **_ERR_NOT_FOUND},
)
async def get_patient_core(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Fetches the patient (scalars only) scoped to the caller's org —
    get_patient_scoped() raises PermissionDeniedError (403) outright for an
    org-less token, or NotFoundError (404) if it belongs to a different org."""
    patient = await patient_service.get_patient_scoped(
        patient_id, actor.org_id, core=True
    )
    return format_response(
        patient_service._to_fhir_core(patient),
        patient_service._to_plain_core(patient),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{patient_id}",
    operation_id="patch_patient",
    summary="Partially update a Patient resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. "
        "Patchable scalar fields: gender, birth_date, active, deceased, marital status, "
        "multiple birth, managing organization. "
        "To modify sub-resources (names, identifiers, etc.) use the dedicated endpoints. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_patient(
    payload: PatientPatchSchema,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of core scalar fields only — sub-resources untouched.
    updated_by comes from the verified JWT (actor.sub); patch_patient()
    raises NotFoundError (404, not 403 — avoids leaking that a patient with
    this id exists in another org) if actor.org_id doesn't match."""
    updated = await patient_service.patch_patient(
        patient_id, payload, actor.sub, actor.org_id
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.patch(
    "/{patient_id}/full",
    operation_id="patch_patient_full",
    summary="Atomically update a Patient and replace any sub-resource lists in one request",
    description=(
        "Patches a Patient's scalar fields (same semantics as `PATCH /{patient_id}`) AND "
        "replaces sub-resource lists atomically in a single DB transaction. "
        "For each list that is **provided** (even `[]`): all existing rows are deleted and the "
        "new items are inserted. Lists that are **omitted** (null / not in body) are left untouched. "
        "Contacts with nested relationship / telecom grandchildren are handled correctly. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_patient_full(
    payload: PatientFullPatchSchema,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of core scalar fields plus atomic replacement of any
    supplied sub-resource lists. Same actor-derived updated_by and org_id
    ownership gate as patch_patient — patch_patient_full() raises
    NotFoundError (404) on mismatch."""
    updated = await patient_service.patch_patient_full(
        patient_id, payload, actor.sub, actor.org_id
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_patients",
    summary="List all Patient resources",
    description=(
        "Returns a paginated list of Patient resources, matching the FHIR R4 Patient "
        "search parameter set. "
        "Filter by `family`/`given` (partial match on one HumanName sub-field) or `name` "
        "(partial match across family/given/prefix/suffix/text combined), `identifier` "
        "(exact business-identifier value), `gender`, `active`, `deceased` (true = "
        "deceased[x] is populated at all, boolean or date), "
        "`birthdate`/`death-date` (FHIR comparator-prefixed date, e.g. `ge2020-01-01`; "
        "repeat the param for a range), "
        "`address` (partial match across every Address sub-field) or "
        "`address-city`/`address-state`/`address-postalcode`/`address-country`/`address-use` "
        "(one specific sub-field), `telecom` (any system) or `email`/`phone` (one system), "
        "`language` (Patient.communication.language code), "
        "`general-practitioner`/`organization`/`link` (FHIR reference string, e.g. "
        "`Organization/190001`), or `user_id`. "
        "Always scoped to the caller's own org (from the verified token) — `org_id` is "
        "not a client-suppliable filter. "
        "Sort with `sort` (e.g. `-birth_date`); set `total_mode=none` to skip the COUNT(*) "
        "on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_patients(
    request: Request,
    actor: AuthUser = Depends(require_permission("patient", "read")),
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
    gender: PatientGender | None = Query(None, description="male|female|other|unknown"),
    active: bool | None = Query(None),
    user_id: str | None = Query(None),
    identifier: str | None = Query(
        None, description="Exact match on a business identifier value (MRN, SSN, etc.)."
    ),
    birthdate: list[_FhirDateItem] | None = Query(
        None,
        description=(
            "FHIR comparator-prefixed date (eq/ne/gt/lt/ge/le), e.g. `ge2020-01-01`. "
            "Repeat the param for a range, e.g. `birthdate=ge2020-01-01&birthdate=le2020-12-31`."
        ),
    ),
    death_date: list[_FhirDateItem] | None = Query(
        None,
        alias="death-date",
        description="Same comparator-prefixed format as birthdate, filtering on the deceased dateTime.",
    ),
    deceased: bool | None = Query(
        None,
        description="true = deceased[x] is populated at all (boolean true or a death date present).",
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
    language: str | None = Query(
        None,
        description="Exact match on Patient.communication.language code (e.g. en, fr).",
    ),
    general_practitioner: str | None = Query(
        None,
        alias="general-practitioner",
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Practitioner/30001`.",
    ),
    organization: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="managingOrganization as a FHIR reference string, e.g. `Organization/190001`.",
    ),
    link: str | None = Query(
        None,
        pattern=_FHIR_REFERENCE_PATTERN,
        description="FHIR reference string, e.g. `Patient/10002` or `RelatedPerson/300001`.",
    ),
    params: ListParams = Depends(),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Every filter param is forwarded straight through to the repository's
    list() — see the route description for the full filter set. org_id is
    always the caller's own (actor.org_id), never client-suppliable;
    list_patients() raises PermissionDeniedError (403) outright for an
    org-less token."""
    patients, total = await patient_service.list_patients(
        user_id=user_id,
        org_id=actor.org_id,
        family=family,
        given=given,
        name=name,
        gender=gender,
        active=active,
        identifier=identifier,
        birthdate=birthdate,
        death_date=death_date,
        deceased=deceased,
        address=address,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
        address_use=address_use,
        telecom=telecom,
        email=email,
        phone=phone,
        language=language,
        general_practitioner=general_practitioner,
        organization=organization,
        link=link,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [patient_service._to_fhir(p) for p in patients],
        [patient_service._to_plain(p) for p in patients],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient",
    summary="Delete a Patient resource",
    description="Permanently deletes the Patient and all associated sub-resources. Returns 204 on success.",
    responses={**_ERR_NOT_FOUND},
)
async def delete_patient(
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_patient() raises NotFoundError (404) if the id doesn't exist at
    all, or if it exists but belongs to a different org. Delete cascades to
    every sub-resource row."""
    await patient_service.delete_patient(patient_id, actor.org_id)
