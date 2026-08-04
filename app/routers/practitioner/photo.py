from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.practitioner import get_practitioner_service
from app.fhir.datatypes import fhir_photo
from app.fhir.mappers.practitioner import plain_photo
from app.schemas.practitioner import PractitionerPhotoCreate, PractitionerPhotoPatch
from app.services.practitioner import PractitionerService

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
    "/{practitioner_id}/photos",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_practitioner_photo",
    summary="Add a photo (Attachment) to a Practitioner",
    description=(
        "Appends a photo attachment to the Practitioner. "
        "Provide `data` (base64-encoded image) or `url` pointing to the image, "
        "plus `content_type` (MIME type, e.g. `image/png`). "
        "Returns the full updated Practitioner resource. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new photo appended",
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_photo(
    payload: PractitionerPhotoCreate,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_photo(
        practitioner_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


@router.get(
    "/{practitioner_id}/photos",
    operation_id="list_practitioner_photos",
    summary="List all photos for a Practitioner",
    description=(
        "Returns all photo attachments stored for this Practitioner. "
        "Each item includes `id` — use it to remove a specific photo via "
        "`DELETE /{practitioner_id}/photos/{photo_id}`."
    ),
    responses={**_SUBRES_PHOTOS_200, **_ERR_NOT_FOUND},
)
async def list_photos(
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    items = await practitioner_service.get_photos(
        practitioner_id, org_id=actor.org_id
    )
    plain = [plain_photo(p) for p in items]
    if wants_fhir(request):
        fhir = [{"id": p.id, **fhir_photo(p)} for p in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{practitioner_id}/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_photo",
    summary="Remove a photo from a Practitioner",
    description=(
        "Permanently deletes a single photo attachment. "
        "The `photo_id` is the `id` returned by `GET /{practitioner_id}/photos`. "
        "Returns 404 if the photo does not exist or belongs to a different Practitioner."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_photo(
    photo_id: int,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    await practitioner_service.delete_photo(
        practitioner_id, photo_id, org_id=actor.org_id
    )


@router.patch(
    "/{practitioner_id}/photos/{photo_id}",
    operation_id="patch_practitioner_photo",
    summary="Update a photo attachment on a Practitioner",
    description=(
        "Partially updates a single photo attachment. Only supplied fields are written. "
        "The `photo_id` is the `id` returned by `GET /{practitioner_id}/photos`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_photo(
    photo_id: int,
    payload: PractitionerPhotoPatch,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.patch_photo(
        practitioner_id,
        photo_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
