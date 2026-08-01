from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.practitioner import get_practitioner_service
from app.fhir.mappers.practitioner import fhir_identifier, plain_identifier
from app.schemas.practitioner import (
    PractitionerIdentifierCreate,
    PractitionerIdentifierPatch,
)
from app.services.practitioner_service import PractitionerService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_IDENTIFIERS_200,
)

router = APIRouter()


@router.post(
    "/{practitioner_id}/identifiers",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_practitioner_identifier",
    summary="Add a business identifier to a Practitioner (e.g. NPI, license, DEA)",
    description=(
        "Appends a business identifier to the Practitioner. "
        "`system` is a URI namespace (e.g. `http://hl7.org/fhir/sid/us-npi`); "
        "`value` is the identifier string within that namespace. "
        "Optional `type_system`, `type_code`, `type_display`, `type_text` describe the identifier category. "
        "Returns the full updated Practitioner resource. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new identifier appended",
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_identifier(
    payload: PractitionerIdentifierCreate,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_identifier(
        practitioner_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


@router.get(
    "/{practitioner_id}/identifiers",
    operation_id="list_practitioner_identifiers",
    summary="List all business identifiers for a Practitioner",
    description=(
        "Returns all business identifiers (NPI, DEA, license numbers, etc.) attached to this Practitioner. "
        "Each item includes `id` — use it to remove a specific identifier via "
        "`DELETE /{practitioner_id}/identifiers/{identifier_id}`."
    ),
    responses={**_SUBRES_IDENTIFIERS_200, **_ERR_NOT_FOUND},
)
async def list_identifiers(
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    items = await practitioner_service.get_identifiers(
        practitioner_id, org_id=actor.org_id
    )
    plain = [plain_identifier(i) for i in items]
    if wants_fhir(request):
        fhir = [{"id": i.id, **fhir_identifier(i)} for i in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{practitioner_id}/identifiers/{identifier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_identifier",
    summary="Remove a business identifier from a Practitioner",
    description=(
        "Permanently deletes a single business identifier. "
        "The `identifier_id` is the `id` returned by `GET /{practitioner_id}/identifiers`. "
        "Returns 404 if the identifier does not exist or belongs to a different Practitioner."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_identifier(
    identifier_id: int,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    await practitioner_service.delete_identifier(
        practitioner_id, identifier_id, org_id=actor.org_id
    )


@router.patch(
    "/{practitioner_id}/identifiers/{identifier_id}",
    operation_id="patch_practitioner_identifier",
    summary="Update a business identifier on a Practitioner",
    description=(
        "Partially updates a single business identifier. Only supplied fields are written. "
        "The `identifier_id` is the `id` returned by `GET /{practitioner_id}/identifiers`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_identifier(
    identifier_id: int,
    payload: PractitionerIdentifierPatch,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.patch_identifier(
        practitioner_id,
        identifier_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
