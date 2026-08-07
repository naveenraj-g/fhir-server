from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.core.logging import get_logger, log_payload
from app.di.dependencies.practitioner import get_practitioner_service
from app.fhir.datatypes import fhir_telecom
from app.fhir.mappers.practitioner import plain_telecom
from app.schemas.practitioner import PractitionerTelecomCreate, PractitionerTelecomPatch
from app.services.practitioner import PractitionerService

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
    "/{practitioner_id}/telecom",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_practitioner_telecom",
    summary="Add a contact point (telecom) to a Practitioner",
    description=(
        "Appends a contact point to the Practitioner. "
        "`system`: phone | fax | email | pager | url | sms | other. "
        "`use`: home | work | temp | old | mobile. "
        "Returns the full updated Practitioner resource. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new contact point appended",
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_telecom(
    payload: PractitionerTelecomCreate,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Add a contact point (telecom) to a Practitioner",
        extra={"event": "route.add_practitioner_telecom", "practitioner_id": practitioner_id},
    )
    log_payload(logger, "practitioner.telecom.add.payload", payload)
    updated = await practitioner_service.add_telecom(
        practitioner_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


@router.get(
    "/{practitioner_id}/telecom",
    operation_id="list_practitioner_telecom",
    summary="List all contact points (telecom) for a Practitioner",
    description=(
        "Returns all contact points (phone, email, fax, pager, etc.) for this Practitioner. "
        "Each item includes `id` — use it to remove a specific contact point via "
        "`DELETE /{practitioner_id}/telecom/{telecom_id}`."
    ),
    responses={**_SUBRES_TELECOM_200, **_ERR_NOT_FOUND},
)
async def list_telecom(
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "List all contact points (telecom) for a Practitioner",
        extra={"event": "route.list_practitioner_telecom", "practitioner_id": practitioner_id},
    )
    items = await practitioner_service.get_telecoms(
        practitioner_id, org_id=actor.org_id
    )
    plain = [plain_telecom(t) for t in items]
    if wants_fhir(request):
        fhir = [{"id": t.id, **fhir_telecom(t)} for t in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{practitioner_id}/telecom/{telecom_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_telecom",
    summary="Remove a contact point from a Practitioner",
    description=(
        "Permanently deletes a single contact point (phone, email, etc.). "
        "The `telecom_id` is the `id` returned by `GET /{practitioner_id}/telecom`. "
        "Returns 404 if the contact point does not exist or belongs to a different Practitioner."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_telecom(
    telecom_id: int,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Remove a contact point from a Practitioner",
        extra={"event": "route.delete_practitioner_telecom", "telecom_id": telecom_id, "practitioner_id": practitioner_id},
    )
    await practitioner_service.delete_telecom(
        practitioner_id, telecom_id, org_id=actor.org_id
    )


@router.patch(
    "/{practitioner_id}/telecom/{telecom_id}",
    operation_id="patch_practitioner_telecom",
    summary="Update a contact point on a Practitioner",
    description=(
        "Partially updates a single contact point (phone, email, etc.). Only supplied fields are written. "
        "The `telecom_id` is the `id` returned by `GET /{practitioner_id}/telecom`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_telecom(
    telecom_id: int,
    payload: PractitionerTelecomPatch,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Update a contact point on a Practitioner",
        extra={"event": "route.patch_practitioner_telecom", "telecom_id": telecom_id, "practitioner_id": practitioner_id},
    )
    log_payload(logger, "practitioner.telecom.patch.payload", payload)
    updated = await practitioner_service.patch_telecom(
        practitioner_id,
        telecom_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
