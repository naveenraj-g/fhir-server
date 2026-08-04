from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.di.dependencies.patient import get_patient_service
from app.fhir.mappers.patient import fhir_identifier, plain_identifier
from app.schemas.patient import IdentifierCreate, IdentifierPatch
from app.services.patient import PatientService

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
    "/{patient_id}/identifiers",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_identifier",
    summary="Add an identifier to a Patient",
    description=(
        "Appends a business identifier (e.g. MRN, SSN, passport). "
        "`system` is a URI namespace; `value` is the identifier string within that namespace. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_identifier(
    payload: IdentifierCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one identifier row, then return the full updated Patient."""
    updated = await patient_service.add_identifier(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/identifiers",
    operation_id="list_patient_identifiers",
    summary="List all business identifiers for a Patient",
    description=(
        "Returns all business identifiers (e.g. MRN, social security, passport) attached to this Patient. "
        "Each item includes `id` — use it to remove a specific identifier via "
        "`DELETE /{patient_id}/identifiers/{identifier_id}`."
    ),
    responses={**_SUBRES_IDENTIFIERS_200, **_ERR_NOT_FOUND},
)
async def list_identifiers(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the shared fhir_identifier()/plain_identifier() mappers directly — bypasses
    the service's _to_fhir/_to_plain since this returns a bare list, not a full Patient."""
    items = await patient_service.get_identifiers(
        patient_id, org_id=actor.org_id
    )
    plain = [plain_identifier(i) for i in items]
    if wants_fhir(request):
        fhir = [{"id": i.id, **fhir_identifier(i)} for i in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/identifiers/{identifier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_identifier",
    summary="Remove a business identifier from a Patient",
    description=(
        "Permanently deletes a single business identifier. "
        "The `identifier_id` is the `id` returned by `GET /{patient_id}/identifiers`. "
        "Returns 404 if the identifier does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_identifier(
    identifier_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_identifier() raises NotFoundError (404) if the Patient is
    missing, belongs to a different org, or identifier_id doesn't belong to it."""
    await patient_service.delete_identifier(
        patient_id, identifier_id, org_id=actor.org_id
    )


@router.patch(
    "/{patient_id}/identifiers/{identifier_id}",
    operation_id="patch_patient_identifier",
    summary="Update a business identifier on a Patient",
    description=(
        "Partially updates a single business identifier. Only supplied fields are written. "
        "The `identifier_id` is the `id` returned by `GET /{patient_id}/identifiers`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_identifier(
    identifier_id: int,
    payload: IdentifierPatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one identifier row, then return the full updated
    Patient. patch_identifier() raises NotFoundError (404) if the Patient is
    missing, belongs to a different org, or identifier_id doesn't belong to it."""
    updated = await patient_service.patch_identifier(
        patient_id,
        identifier_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
