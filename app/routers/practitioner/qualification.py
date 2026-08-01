from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_response, wants_fhir
from app.deps.practitioner_deps import resolve_practitioner
from app.di.dependencies.practitioner import get_practitioner_service
from app.fhir.mappers.practitioner import fhir_qualification, plain_qualification
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import (
    PractitionerQualificationCreate,
    PractitionerQualificationPatch,
)
from app.services.practitioner_service import PractitionerService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _SINGLE_200,
    _SINGLE_201,
    _SUBRES_QUALIFICATIONS_200,
)

router = APIRouter()


@router.post(
    "/{practitioner_id}/qualifications",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_practitioner_qualification",
    summary="Add a professional qualification to a Practitioner",
    description=(
        "Records a degree, certification, accreditation, or license held by the Practitioner "
        "(e.g. MD, board certification, NPI, DEA number). "
        "Provide `code_system`, `code_code`, `code_display` for the qualification type "
        "(e.g. SNOMED CT code for MD), an optional validity `period`, and optional `issuer_id` / `issuer_display`. "
        "Returns the full updated Practitioner resource. " + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new qualification appended",
    responses={**_SINGLE_201, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_qualification(
    payload: PractitionerQualificationCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(resolve_practitioner),
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_qualification(
        practitioner.practitioner_id, payload, org_id=actor.org_id, created_by=actor.sub
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


@router.get(
    "/{practitioner_id}/qualifications",
    operation_id="list_practitioner_qualifications",
    summary="List all qualifications for a Practitioner",
    description=(
        "Returns all degrees, certifications, accreditations, and licenses for this Practitioner "
        "(e.g. MD, board certification, NPI, DEA number). "
        "Each qualification includes its nested identifiers and issuing organization reference. "
        "Each item includes `id` — use it to remove a specific qualification via "
        "`DELETE /{practitioner_id}/qualifications/{qualification_id}`."
    ),
    responses={**_SUBRES_QUALIFICATIONS_200, **_ERR_NOT_FOUND},
)
async def list_qualifications(
    request: Request,
    practitioner: PractitionerModel = Depends(resolve_practitioner),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    items = await practitioner_service.get_qualifications(
        practitioner.practitioner_id, org_id=actor.org_id
    )
    plain = [plain_qualification(q) for q in items]
    if wants_fhir(request):
        fhir = [{"id": q.id, **fhir_qualification(q)} for q in items]
        return JSONResponse(
            {"data": fhir, "total": len(fhir)}, media_type="application/fhir+json"
        )
    return JSONResponse({"data": plain, "total": len(plain)})


@router.delete(
    "/{practitioner_id}/qualifications/{qualification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner_qualification",
    summary="Remove a qualification from a Practitioner",
    description=(
        "Permanently deletes a single qualification and all its nested identifiers. "
        "The `qualification_id` is the `id` returned by `GET /{practitioner_id}/qualifications`. "
        "Returns 404 if the qualification does not exist or belongs to a different Practitioner."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_qualification(
    qualification_id: int,
    practitioner: PractitionerModel = Depends(resolve_practitioner),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    await practitioner_service.delete_qualification(
        practitioner.practitioner_id, qualification_id, org_id=actor.org_id
    )


@router.patch(
    "/{practitioner_id}/qualifications/{qualification_id}",
    operation_id="patch_practitioner_qualification",
    summary="Update a qualification on a Practitioner",
    description=(
        "Partially updates a single qualification. Only supplied fields are written. "
        "If `identifier` is supplied, all existing qualification identifiers are replaced. "
        "The `qualification_id` is the `id` returned by `GET /{practitioner_id}/qualifications`. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_qualification(
    qualification_id: int,
    payload: PractitionerQualificationPatch,
    request: Request,
    practitioner: PractitionerModel = Depends(resolve_practitioner),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.patch_qualification(
        practitioner.practitioner_id,
        qualification_id,
        payload,
        org_id=actor.org_id,
        updated_by=actor.sub,
    )
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
