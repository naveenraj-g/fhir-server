from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.patient import get_patient_service
from app.fhir.mappers.patient import (
    fhir_general_practitioner,
    plain_general_practitioner,
)
from app.schemas.patient import GeneralPractitionerCreate, GeneralPractitionerPatch
from app.services.patient_service import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_GPS_200,
)

router = APIRouter()


@router.post(
    "/{patient_id}/general-practitioners",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_general_practitioner",
    summary="Add a general practitioner reference to a Patient",
    description=(
        "Appends a reference to the patient's nominated primary care provider. "
        "`reference_type`: Organization|Practitioner|PractitionerRole. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_general_practitioner(
    payload: GeneralPractitionerCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one general-practitioner reference row, then return the full updated Patient."""
    updated = await patient_service.add_general_practitioner(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/general-practitioners",
    operation_id="list_patient_general_practitioners",
    summary="List all general practitioner references for a Patient",
    description=(
        "Returns all nominated primary care provider references for this Patient. "
        "Reference types: Organization, Practitioner, PractitionerRole. "
        "Each item includes `id` — use it to remove a specific reference via "
        "`DELETE /{patient_id}/general-practitioners/{gp_id}`."
    ),
    responses={**_SUBRES_GPS_200, **_ERR_NOT_FOUND},
)
async def list_general_practitioners(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the Patient-specific fhir_general_practitioner()/plain_general_practitioner() mappers directly."""
    items = await patient_service.get_general_practitioners(
        patient_id, org_id=actor.org_id
    )
    plain = [plain_general_practitioner(gp) for gp in items]
    if wants_fhir(request):
        fhir = [{"id": gp.id, **fhir_general_practitioner(gp)} for gp in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/general-practitioners/{gp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_general_practitioner",
    summary="Remove a general practitioner reference from a Patient",
    description=(
        "Permanently deletes a single general practitioner reference. "
        "The `gp_id` is the `id` returned by `GET /{patient_id}/general-practitioners`. "
        "Returns 404 if the reference does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_general_practitioner(
    gp_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_general_practitioner() raises NotFoundError (404) if the
    Patient is missing, belongs to a different org, or gp_id doesn't belong
    to it."""
    await patient_service.delete_general_practitioner(
        patient_id, gp_id, org_id=actor.org_id
    )


@router.patch(
    "/{patient_id}/general-practitioners/{gp_id}",
    operation_id="patch_patient_general_practitioner",
    summary="Update a general practitioner reference on a Patient",
    description=(
        "Partially updates a single general practitioner reference. Only supplied fields are written. "
        "The `gp_id` is the `id` returned by `GET /{patient_id}/general-practitioners`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_general_practitioner(
    gp_id: int,
    payload: GeneralPractitionerPatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one general-practitioner reference row, then return
    the full updated Patient. patch_general_practitioner() raises
    NotFoundError (404) if the Patient is missing, belongs to a different
    org, or gp_id doesn't belong to it."""
    updated = await patient_service.patch_general_practitioner(
        patient_id, gp_id, payload, org_id=actor.org_id, updated_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
