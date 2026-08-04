from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.patient import get_patient_service
from app.fhir.datatypes import fhir_address
from app.fhir.mappers.patient import plain_address
from app.schemas.patient import AddressCreate, AddressPatch
from app.services.patient import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_ADDRESSES_200,
)

router = APIRouter()


@router.post(
    "/{patient_id}/addresses",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_address",
    summary="Add an address to a Patient",
    description=(
        "Appends an address. `use`: home|work|temp|old|billing. `type`: postal|physical|both. "
        "`line` accepts a list of address lines. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_address(
    payload: AddressCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one address row, then return the full updated Patient."""
    updated = await patient_service.add_address(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/addresses",
    operation_id="list_patient_addresses",
    summary="List all addresses for a Patient",
    description=(
        "Returns all postal and physical addresses attached to this Patient. "
        "Each item includes `id` — use it to remove a specific address via "
        "`DELETE /{patient_id}/addresses/{address_id}`."
    ),
    responses={**_SUBRES_ADDRESSES_200, **_ERR_NOT_FOUND},
)
async def list_addresses(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the shared fhir_address()/plain_address() mappers directly."""
    items = await patient_service.get_addresses(patient_id, org_id=actor.org_id)
    plain = [plain_address(a) for a in items]
    if wants_fhir(request):
        fhir = [{"id": a.id, **fhir_address(a)} for a in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_address",
    summary="Remove an address from a Patient",
    description=(
        "Permanently deletes a single address entry. "
        "The `address_id` is the `id` returned by `GET /{patient_id}/addresses`. "
        "Returns 404 if the address does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_address(
    address_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_address() raises NotFoundError (404) if the Patient is missing,
    belongs to a different org, or address_id doesn't belong to it."""
    await patient_service.delete_address(
        patient_id, address_id, org_id=actor.org_id
    )


@router.patch(
    "/{patient_id}/addresses/{address_id}",
    operation_id="patch_patient_address",
    summary="Update an address on a Patient",
    description=(
        "Partially updates a single address entry. Only supplied fields are written. "
        "The `address_id` is the `id` returned by `GET /{patient_id}/addresses`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_address(
    address_id: int,
    payload: AddressPatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one address row, then return the full updated
    Patient. patch_address() raises NotFoundError (404) if the Patient is
    missing, belongs to a different org, or address_id doesn't belong to it."""
    updated = await patient_service.patch_address(
        patient_id,
        address_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
