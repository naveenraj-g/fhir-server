from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.patient import get_patient_service
from app.fhir.mappers.patient import fhir_contact, plain_contact
from app.schemas.patient import ContactCreate, ContactPatch
from app.services.patient import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_CONTACTS_200,
)

router = APIRouter()


@router.post(
    "/{patient_id}/contacts",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_contact",
    summary="Add a contact (next-of-kin / guardian) to a Patient",
    description=(
        "Appends a contact BackboneElement. Accepts flattened name and address fields, "
        "plus nested `relationship[]` and `telecom[]` arrays. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_contact(
    payload: ContactCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one contact row (plus its relationship[]/telecom[] grandchildren), then return the full updated Patient."""
    updated = await patient_service.add_contact(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/contacts",
    operation_id="list_patient_contacts",
    summary="List all contacts (next-of-kin / guardian) for a Patient",
    description=(
        "Returns all contact BackboneElements (next-of-kin, guardians, emergency contacts) for this Patient. "
        "Each item includes `id` — use it to remove a specific contact via "
        "`DELETE /{patient_id}/contacts/{contact_id}`."
    ),
    responses={**_SUBRES_CONTACTS_200, **_ERR_NOT_FOUND},
)
async def list_contacts(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the Patient-specific fhir_contact()/plain_contact() mappers directly (not the shared datatypes.py helpers)."""
    items = await patient_service.get_contacts(patient_id, org_id=actor.org_id)
    plain = [plain_contact(c) for c in items]
    if wants_fhir(request):
        fhir = [{"id": c.id, **fhir_contact(c)} for c in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_contact",
    summary="Remove a contact entry from a Patient",
    description=(
        "Permanently deletes a single contact (next-of-kin, guardian, emergency contact). "
        "The `contact_id` is the `id` returned by `GET /{patient_id}/contacts`. "
        "Cascades to all nested relationship, telecom, additional name, and additional address rows. "
        "Returns 404 if the contact does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_contact(
    contact_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_contact() raises NotFoundError (404) if the Patient is missing,
    belongs to a different org, or contact_id doesn't belong to it; cascades
    to its grandchildren."""
    await patient_service.delete_contact(
        patient_id, contact_id, org_id=actor.org_id
    )


@router.patch(
    "/{patient_id}/contacts/{contact_id}",
    operation_id="patch_patient_contact",
    summary="Update a contact entry on a Patient",
    description=(
        "Partially updates a single contact (next-of-kin / guardian). Only supplied fields are written. "
        "If `relationship` is supplied, all existing relationship entries are replaced. "
        "If `telecom` is supplied, all existing contact telecoms are replaced. "
        "The `contact_id` is the `id` returned by `GET /{patient_id}/contacts`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_contact(
    contact_id: int,
    payload: ContactPatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one contact row — replaces relationship[]/telecom[]
    wholesale if supplied, then return the full updated Patient.
    patch_contact() raises NotFoundError (404) if the Patient is missing,
    belongs to a different org, or contact_id doesn't belong to it."""
    updated = await patient_service.patch_contact(
        patient_id,
        contact_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
