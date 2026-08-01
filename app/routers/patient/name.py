from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.patient import get_patient_service
from app.fhir.datatypes import fhir_human_name
from app.fhir.mappers.patient import plain_name
from app.schemas.patient import NameCreate, NamePatch
from app.services.patient_service import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_NAMES_200,
)

router = APIRouter()


@router.post(
    "/{patient_id}/names",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_name",
    summary="Add a name to a Patient",
    description=(
        "Appends a HumanName record to the Patient. "
        "`use` values: usual|official|temp|nickname|anonymous|old|maiden. "
        "`given`, `prefix`, `suffix` accept lists of strings. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_name(
    payload: NameCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one HumanName row, then return the full updated Patient.
    add_name() raises NotFoundError (404) if the patient belongs to a
    different org."""
    updated = await patient_service.add_name(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/names",
    operation_id="list_patient_names",
    summary="List all names for a Patient",
    description=(
        "Returns all HumanName entries attached to this Patient. "
        "Each item includes `id` — use it to remove a specific name via "
        "`DELETE /{patient_id}/names/{name_id}`."
    ),
    responses={**_SUBRES_NAMES_200, **_ERR_NOT_FOUND},
)
async def list_names(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the shared fhir_human_name()/plain_name() mappers directly — bypasses
    the service's _to_fhir/_to_plain since this returns a bare list, not a full Patient."""
    items = await patient_service.get_names(patient_id, org_id=actor.org_id)
    plain = [plain_name(n) for n in items]
    if wants_fhir(request):
        fhir = [{"id": n.id, **fhir_human_name(n)} for n in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/names/{name_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_name",
    summary="Remove a name entry from a Patient",
    description=(
        "Permanently deletes a single HumanName entry. "
        "The `name_id` is the `id` returned by `GET /{patient_id}/names`. "
        "Returns 404 if the name does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_name(
    name_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_name() raises NotFoundError (404) if the Patient is missing,
    belongs to a different org, or if name_id doesn't belong to it."""
    await patient_service.delete_name(patient_id, name_id, org_id=actor.org_id)


@router.patch(
    "/{patient_id}/names/{name_id}",
    operation_id="patch_patient_name",
    summary="Update a name entry on a Patient",
    description=(
        "Partially updates a single HumanName entry. Only supplied fields are written; omitted fields are left unchanged. "
        "The `name_id` is the `id` returned by `GET /{patient_id}/names`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_name(
    name_id: int,
    payload: NamePatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one HumanName row, then return the full updated
    Patient. patch_name() raises NotFoundError (404) if the Patient is
    missing, belongs to a different org, or name_id doesn't belong to it."""
    updated = await patient_service.patch_name(
        patient_id, name_id, payload, org_id=actor.org_id, updated_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
