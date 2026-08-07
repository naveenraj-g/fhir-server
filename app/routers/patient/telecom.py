from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.core.logging import get_logger, log_payload
from app.di.dependencies.patient import get_patient_service
from app.fhir.datatypes import fhir_telecom
from app.fhir.mappers.patient import plain_telecom
from app.schemas.patient import TelecomCreate, TelecomPatch
from app.services.patient import PatientService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_TELECOM_200,
)

router = APIRouter()

logger = get_logger(__name__)


@router.post(
    "/{patient_id}/telecom",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_patient_telecom",
    summary="Add a contact point (telecom) to a Patient",
    description=(
        "Appends a contact point. `system`: phone|fax|email|pager|url|sms|other. "
        "`use`: home|work|temp|old|mobile. `rank`: preferred order (1 = highest). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_telecom(
    payload: TelecomCreate,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "create")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Append one contact-point row, then return the full updated Patient."""
    logger.info(
        "Add a contact point (telecom) to a Patient",
        extra={"event": "route.add_patient_telecom", "patient_id": patient_id},
    )
    log_payload(logger, "patient.telecom.add.payload", payload)
    updated = await patient_service.add_telecom(
        patient_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )


@router.get(
    "/{patient_id}/telecom",
    operation_id="list_patient_telecom",
    summary="List all contact points (telecom) for a Patient",
    description=(
        "Returns all contact points (phone, email, fax, etc.) attached to this Patient. "
        "Each item includes `id` — use it to remove a specific contact point via "
        "`DELETE /{patient_id}/telecom/{telecom_id}`."
    ),
    responses={**_SUBRES_TELECOM_200, **_ERR_NOT_FOUND},
)
async def list_telecom(
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "read")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Calls the shared fhir_telecom()/plain_telecom() mappers directly."""
    logger.info(
        "List all contact points (telecom) for a Patient",
        extra={"event": "route.list_patient_telecom", "patient_id": patient_id},
    )
    items = await patient_service.get_telecoms(patient_id, org_id=actor.org_id)
    plain = [plain_telecom(t) for t in items]
    if wants_fhir(request):
        fhir = [{"id": t.id, **fhir_telecom(t)} for t in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{patient_id}/telecom/{telecom_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_telecom",
    summary="Remove a contact point from a Patient",
    description=(
        "Permanently deletes a single contact point (phone, email, etc.). "
        "The `telecom_id` is the `id` returned by `GET /{patient_id}/telecom`. "
        "Returns 404 if the contact point does not exist or belongs to a different Patient."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_telecom(
    telecom_id: int,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "delete")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """delete_telecom() raises NotFoundError (404) if the Patient is missing,
    belongs to a different org, or telecom_id doesn't belong to it."""
    logger.info(
        "Remove a contact point from a Patient",
        extra={"event": "route.delete_patient_telecom", "telecom_id": telecom_id, "patient_id": patient_id},
    )
    await patient_service.delete_telecom(
        patient_id, telecom_id, org_id=actor.org_id
    )


@router.patch(
    "/{patient_id}/telecom/{telecom_id}",
    operation_id="patch_patient_telecom",
    summary="Update a contact point on a Patient",
    description=(
        "Partially updates a single contact point (phone, email, etc.). Only supplied fields are written. "
        "The `telecom_id` is the `id` returned by `GET /{patient_id}/telecom`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_telecom(
    telecom_id: int,
    payload: TelecomPatch,
    request: Request,
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    actor: AuthUser = Depends(require_permission("patient", "update")),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Partial update of one contact-point row, then return the full updated
    Patient. patch_telecom() raises NotFoundError (404) if the Patient is
    missing, belongs to a different org, or telecom_id doesn't belong to it."""
    logger.info(
        "Update a contact point on a Patient",
        extra={"event": "route.patch_patient_telecom", "telecom_id": telecom_id, "patient_id": patient_id},
    )
    log_payload(logger, "patient.telecom.patch.payload", payload)
    updated = await patient_service.patch_telecom(
        patient_id,
        telecom_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        patient_service._to_fhir(updated), patient_service._to_plain(updated), request
    )
