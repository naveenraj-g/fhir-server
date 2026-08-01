from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.deps.practitioner_deps import resolve_practitioner
from app.di.dependencies.practitioner import get_practitioner_service
from app.fhir.datatypes import fhir_human_name
from app.fhir.mappers.practitioner import plain_name
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerNameCreate, PractitionerNamePatch
from app.services.practitioner_service import PractitionerService

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
    "/{practitioner_id}/names",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_practitioner_name",
    summary="Add a HumanName to a Practitioner",
    description=(
        "Appends a name to the Practitioner. "
        "Supports `use` (usual | official | temp | nickname | anonymous | old | maiden), "
        "`family`, `given[]`, `prefix[]`, `suffix[]`, `text`, and an optional validity `period`. "
        "Returns the full updated Practitioner resource. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new name appended",
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_name(
    payload: PractitionerNameCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(resolve_practitioner),
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_name(
        practitioner.practitioner_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


@router.get(
    "/{practitioner_id}/names",
    operation_id="list_practitioner_names",
    summary="List all HumanName entries for a Practitioner",
    description=(
        "Returns all HumanName entries attached to this Practitioner. "
        "Each item includes `id` — use it to remove a specific name via "
        "`DELETE /{practitioner_id}/names/{name_id}`."
    ),
    responses={**_SUBRES_NAMES_200, **_ERR_NOT_FOUND},
)
async def list_names(
    request: Request,
    practitioner: PractitionerModel = Depends(resolve_practitioner),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    items = await practitioner_service.get_names(
        practitioner.practitioner_id, org_id=actor.org_id
    )
    plain = [plain_name(n) for n in items]
    if wants_fhir(request):
        fhir = [{"id": n.id, **fhir_human_name(n)} for n in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{practitioner_id}/names/{name_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_name",
    summary="Remove a HumanName entry from a Practitioner",
    description=(
        "Permanently deletes a single HumanName entry. "
        "The `name_id` is the `id` returned by `GET /{practitioner_id}/names`. "
        "Returns 404 if the name does not exist or belongs to a different Practitioner."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_name(
    name_id: int,
    practitioner: PractitionerModel = Depends(resolve_practitioner),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    await practitioner_service.delete_name(
        practitioner.practitioner_id, name_id, org_id=actor.org_id
    )


@router.patch(
    "/{practitioner_id}/names/{name_id}",
    operation_id="patch_practitioner_name",
    summary="Update a name entry on a Practitioner",
    description=(
        "Partially updates a single HumanName entry. Only supplied fields are written; omitted fields are left unchanged. "
        "The `name_id` is the `id` returned by `GET /{practitioner_id}/names`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_name(
    name_id: int,
    payload: PractitionerNamePatch,
    request: Request,
    practitioner: PractitionerModel = Depends(resolve_practitioner),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.patch_name(
        practitioner.practitioner_id,
        name_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
