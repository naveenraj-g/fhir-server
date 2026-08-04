from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.practitioner import get_practitioner_service
from app.fhir.mappers.practitioner import (
    fhir_practitioner_communication,
    plain_practitioner_communication,
)
from app.schemas.practitioner import (
    PractitionerCommunicationCreate,
    PractitionerCommunicationPatch,
)
from app.services.practitioner import PractitionerService

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
    "/{practitioner_id}/communications",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_practitioner_communication",
    summary="Add a communication language to a Practitioner",
    description=(
        "Records a language the Practitioner can use in patient communication. "
        "`language_code` is an ISO-639-1 code (e.g. `en`, `fr`, `de`). "
        "Returns the full updated Practitioner resource. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new communication language appended",
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_communication(
    payload: PractitionerCommunicationCreate,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_communication(
        practitioner_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


@router.get(
    "/{practitioner_id}/communications",
    operation_id="list_practitioner_communications",
    summary="List all communication languages for a Practitioner",
    description=(
        "Returns all languages this Practitioner can use in patient communication. "
        "Each item includes `id` — use it to remove a specific language entry via "
        "`DELETE /{practitioner_id}/communications/{comm_id}`."
    ),
    responses={**_SUBRES_COMMUNICATIONS_200, **_ERR_NOT_FOUND},
)
async def list_communications(
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    items = await practitioner_service.get_communications(
        practitioner_id, org_id=actor.org_id
    )
    plain = [plain_practitioner_communication(c) for c in items]
    if wants_fhir(request):
        fhir = [{"id": c.id, **fhir_practitioner_communication(c)} for c in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{practitioner_id}/communications/{comm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_communication",
    summary="Remove a communication language from a Practitioner",
    description=(
        "Permanently deletes a single communication language entry. "
        "The `comm_id` is the `id` returned by `GET /{practitioner_id}/communications`. "
        "Returns 404 if the entry does not exist or belongs to a different Practitioner."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_communication(
    comm_id: int,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    await practitioner_service.delete_communication(
        practitioner_id, comm_id, org_id=actor.org_id
    )


@router.patch(
    "/{practitioner_id}/communications/{comm_id}",
    operation_id="patch_practitioner_communication",
    summary="Update a communication language on a Practitioner",
    description=(
        "Partially updates a single communication language entry. Only supplied fields are written. "
        "The `comm_id` is the `id` returned by `GET /{practitioner_id}/communications`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_communication(
    comm_id: int,
    payload: PractitionerCommunicationPatch,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.patch_communication(
        practitioner_id,
        comm_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
