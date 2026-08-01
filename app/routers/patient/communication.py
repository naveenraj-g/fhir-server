from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.patient import get_patient_service
from app.fhir.datatypes import fhir_communication
from app.fhir.mappers.patient import plain_communication
from app.schemas.patient import CommunicationCreate, CommunicationPatch
from app.services.patient_service import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_COMMUNICATIONS_200,
)

router = APIRouter()


@router.post(
    "/{patient_id}/communications",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_communication",
    summary="Add a communication language to a Patient",
    description=(
        "Appends a preferred communication language. `language_code` is an ISO-639-1 code (e.g. en, fr). "
        "Set `preferred: true` to mark this as the patient's primary language. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_communication(
    payload: CommunicationCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one communication-language row, then return the full updated Patient."""
    updated = await patient_service.add_communication(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/communications",
    operation_id="list_patient_communications",
    summary="List all communication languages for a Patient",
    description=(
        "Returns all preferred communication language entries for this Patient. "
        "Each item includes `id` — use it to remove a specific language via "
        "`DELETE /{patient_id}/communications/{comm_id}`."
    ),
    responses={**_SUBRES_COMMUNICATIONS_200, **_ERR_NOT_FOUND},
)
async def list_communications(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the shared fhir_communication()/plain_communication() mappers directly."""
    items = await patient_service.get_communications(
        patient_id, org_id=actor.org_id
    )
    plain = [plain_communication(cm) for cm in items]
    if wants_fhir(request):
        fhir = [{"id": cm.id, **fhir_communication(cm)} for cm in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/communications/{comm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_communication",
    summary="Remove a communication language from a Patient",
    description=(
        "Permanently deletes a single communication language entry. "
        "The `comm_id` is the `id` returned by `GET /{patient_id}/communications`. "
        "Returns 404 if the entry does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_communication(
    comm_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_communication() raises NotFoundError (404) if the Patient is
    missing, belongs to a different org, or comm_id doesn't belong to it."""
    await patient_service.delete_communication(
        patient_id, comm_id, org_id=actor.org_id
    )


@router.patch(
    "/{patient_id}/communications/{comm_id}",
    operation_id="patch_patient_communication",
    summary="Update a communication language on a Patient",
    description=(
        "Partially updates a single communication language entry. Only supplied fields are written. "
        "The `comm_id` is the `id` returned by `GET /{patient_id}/communications`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_communication(
    comm_id: int,
    payload: CommunicationPatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one communication-language row, then return the
    full updated Patient. patch_communication() raises NotFoundError (404)
    if the Patient is missing, belongs to a different org, or comm_id
    doesn't belong to it."""
    updated = await patient_service.patch_communication(
        patient_id, comm_id, payload, org_id=actor.org_id, updated_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
