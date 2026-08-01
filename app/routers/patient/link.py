from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.patient import get_patient_service
from app.fhir.mappers.patient import fhir_link, plain_link
from app.schemas.patient import LinkCreate, LinkPatch
from app.services.patient_service import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_LINKS_200,
)

router = APIRouter()


@router.post(
    "/{patient_id}/links",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_link",
    summary="Add a link to a related Patient or RelatedPerson",
    description=(
        "`other_type`: Patient|RelatedPerson. "
        "`type`: replaced-by|replaces|refer|seealso. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_link(
    payload: LinkCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one patient-link row, then return the full updated Patient."""
    updated = await patient_service.add_link(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/links",
    operation_id="list_patient_links",
    summary="List all patient links for a Patient",
    description=(
        "Returns all links to related Patient or RelatedPerson resources. "
        "Link types: replaced-by | replaces | refer | seealso. "
        "Each item includes `id` — use it to remove a specific link via "
        "`DELETE /{patient_id}/links/{link_id}`."
    ),
    responses={**_SUBRES_LINKS_200, **_ERR_NOT_FOUND},
)
async def list_links(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the Patient-specific fhir_link()/plain_link() mappers directly."""
    items = await patient_service.get_links(patient_id, org_id=actor.org_id)
    plain = [plain_link(lk) for lk in items]
    if wants_fhir(request):
        fhir = [{"id": lk.id, **fhir_link(lk)} for lk in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_link",
    summary="Remove a link from a Patient",
    description=(
        "Permanently deletes a single patient link entry. "
        "The `link_id` is the `id` returned by `GET /{patient_id}/links`. "
        "Returns 404 if the link does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_link(
    link_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_link() raises NotFoundError (404) if the Patient is missing,
    belongs to a different org, or link_id doesn't belong to it."""
    await patient_service.delete_link(patient_id, link_id, org_id=actor.org_id)


@router.patch(
    "/{patient_id}/links/{link_id}",
    operation_id="patch_patient_link",
    summary="Update a link entry on a Patient",
    description=(
        "Partially updates a single patient link. Only supplied fields are written. "
        "The `link_id` is the `id` returned by `GET /{patient_id}/links`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_link(
    link_id: int,
    payload: LinkPatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one patient-link row, then return the full updated
    Patient. patch_link() raises NotFoundError (404) if the Patient is
    missing, belongs to a different org, or link_id doesn't belong to it."""
    updated = await patient_service.patch_link(
        patient_id, link_id, payload, org_id=actor.org_id, updated_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
