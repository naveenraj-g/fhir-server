from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.patient import get_patient_service
from app.fhir.datatypes import fhir_photo
from app.fhir.mappers.patient import plain_photo
from app.schemas.patient import PhotoCreate, PhotoPatch
from app.services.patient_service import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_PHOTOS_200,
)

router = APIRouter()


@router.post(
    "/{patient_id}/photos",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_photo",
    summary="Add a photo (Attachment) to a Patient",
    description=(
        "Appends a photo attachment. Provide either `url` (external link) or "
        "`data` (base64-encoded binary). `content_type` is a MIME type (e.g. image/png). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_photo(
    payload: PhotoCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one photo attachment row, then return the full updated Patient."""
    updated = await patient_service.add_photo(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/photos",
    operation_id="list_patient_photos",
    summary="List all photos (Attachments) for a Patient",
    description=(
        "Returns all photo attachments stored for this Patient. "
        "Each item includes `id` — use it to remove a specific photo via "
        "`DELETE /{patient_id}/photos/{photo_id}`."
    ),
    responses={**_SUBRES_PHOTOS_200, **_ERR_NOT_FOUND},
)
async def list_photos(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the shared fhir_photo()/plain_photo() mappers directly."""
    items = await patient_service.get_photos(patient_id, org_id=actor.org_id)
    plain = [plain_photo(p) for p in items]
    if wants_fhir(request):
        fhir = [{"id": p.id, **fhir_photo(p)} for p in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_photo",
    summary="Remove a photo from a Patient",
    description=(
        "Permanently deletes a single photo attachment. "
        "The `photo_id` is the `id` returned by `GET /{patient_id}/photos`. "
        "Returns 404 if the photo does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_photo(
    photo_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_photo() raises NotFoundError (404) if the Patient is missing,
    belongs to a different org, or photo_id doesn't belong to it."""
    await patient_service.delete_photo(
        patient_id, photo_id, org_id=actor.org_id
    )


@router.patch(
    "/{patient_id}/photos/{photo_id}",
    operation_id="patch_patient_photo",
    summary="Update a photo attachment on a Patient",
    description=(
        "Partially updates a single photo attachment. Only supplied fields are written. "
        "The `photo_id` is the `id` returned by `GET /{patient_id}/photos`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_photo(
    photo_id: int,
    payload: PhotoPatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one photo attachment row, then return the full
    updated Patient. patch_photo() raises NotFoundError (404) if the Patient
    is missing, belongs to a different org, or photo_id doesn't belong to it."""
    updated = await patient_service.patch_photo(
        patient_id, photo_id, payload, org_id=actor.org_id, updated_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
