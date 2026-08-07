from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.core.logging import get_logger, log_payload
from app.di.dependencies.practitioner import get_practitioner_service
from app.fhir.datatypes import fhir_address
from app.fhir.mappers.practitioner import plain_address
from app.schemas.practitioner import PractitionerAddressCreate, PractitionerAddressPatch
from app.services.practitioner import PractitionerService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_ADDRESSES_200,
)

router = APIRouter()

logger = get_logger(__name__)


@router.post(
    "/{practitioner_id}/addresses",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_practitioner_address",
    summary="Add an address to a Practitioner",
    description=(
        "Appends a postal or physical address to the Practitioner. "
        "`use`: home | work | temp | old | billing. "
        "`type`: postal | physical | both. "
        "`line` is an array of street address lines. "
        "Returns the full updated Practitioner resource. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new address appended",
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_address(
    payload: PractitionerAddressCreate,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Add an address to a Practitioner",
        extra={"event": "route.add_practitioner_address", "practitioner_id": practitioner_id},
    )
    log_payload(logger, "practitioner.address.add.payload", payload)
    updated = await practitioner_service.add_address(
        practitioner_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


@router.get(
    "/{practitioner_id}/addresses",
    operation_id="list_practitioner_addresses",
    summary="List all addresses for a Practitioner",
    description=(
        "Returns all postal and physical addresses for this Practitioner. "
        "Each item includes `id` — use it to remove a specific address via "
        "`DELETE /{practitioner_id}/addresses/{address_id}`."
    ),
    responses={**_SUBRES_ADDRESSES_200, **_ERR_NOT_FOUND},
)
async def list_addresses(
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "List all addresses for a Practitioner",
        extra={"event": "route.list_practitioner_addresses", "practitioner_id": practitioner_id},
    )
    items = await practitioner_service.get_addresses(
        practitioner_id, org_id=actor.org_id
    )
    plain = [plain_address(a) for a in items]
    if wants_fhir(request):
        fhir = [{"id": a.id, **fhir_address(a)} for a in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{practitioner_id}/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_address",
    summary="Remove an address from a Practitioner",
    description=(
        "Permanently deletes a single address entry. "
        "The `address_id` is the `id` returned by `GET /{practitioner_id}/addresses`. "
        "Returns 404 if the address does not exist or belongs to a different Practitioner."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_address(
    address_id: int,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Remove an address from a Practitioner",
        extra={"event": "route.delete_practitioner_address", "address_id": address_id, "practitioner_id": practitioner_id},
    )
    await practitioner_service.delete_address(
        practitioner_id, address_id, org_id=actor.org_id
    )


@router.patch(
    "/{practitioner_id}/addresses/{address_id}",
    operation_id="patch_practitioner_address",
    summary="Update an address on a Practitioner",
    description=(
        "Partially updates a single address entry. Only supplied fields are written. "
        "The `address_id` is the `id` returned by `GET /{practitioner_id}/addresses`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_address(
    address_id: int,
    payload: PractitionerAddressPatch,
    request: Request,
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Update an address on a Practitioner",
        extra={"event": "route.patch_practitioner_address", "address_id": address_id, "practitioner_id": practitioner_id},
    )
    log_payload(logger, "practitioner.address.patch.payload", payload)
    updated = await practitioner_service.patch_address(
        practitioner_id,
        address_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
