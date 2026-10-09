from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from app.di.dependencies.fhir_profile import get_fhir_profile_service
from app.schemas.fhir_profile import (
    FhirProfileActivateSchema,
    FhirProfileCreateSchema,
    FhirProfileListResponse,
    FhirProfilePatchSchema,
    FhirProfileResponse,
)
from app.services.fhir_profile import FhirProfileService

from ._responses import _LIST_200, _SINGLE_200, _SINGLE_201

router = APIRouter()


@router.post(
    "/",
    operation_id="create_fhir_profile",
    summary="Create a country or organization FHIR profile (as a draft)",
    description=(
        "Creates a scope_level='country' or 'organization' profile row, always as "
        "status='draft'. The parent is resolved automatically — country profiles "
        "link to this resource_type's base profile; organization profiles link to "
        "this deployment's configured country's profile for this resource_type if "
        "one exists, else to base. The candidate structure_definition is run past "
        "the Java validator sidecar's registration check before being persisted; "
        "a rejection returns 422 with the sidecar's own errors. Use the activate "
        "endpoint to make a draft take effect — this endpoint never does."
    ),
    responses={
        **_SINGLE_201,
        422: {
            "description": "Unsupported scope_level, missing scope_id/url, or the sidecar rejected the profile"
        },
    },
)
async def create_fhir_profile(
    body: FhirProfileCreateSchema,
    service: FhirProfileService = Depends(get_fhir_profile_service),
):
    profile = await service.create_profile(
        resource_type=body.resource_type,
        scope_level=body.scope_level,
        scope_id=body.scope_id,
        structure_definition=body.structure_definition,
        created_by=body.created_by,
    )
    return JSONResponse(
        content=jsonable_encoder(FhirProfileResponse.model_validate(profile)),
        status_code=201,
    )


@router.get(
    "/",
    operation_id="list_fhir_profiles",
    summary="List FHIR profiles",
    description="Returns paginated FHIR profile rows across all three scope levels, with optional filters.",
    responses=_LIST_200,
)
async def list_fhir_profiles(
    resource_type: str | None = Query(None),
    scope_level: str | None = Query(
        None, description="'base', 'country', or 'organization'"
    ),
    scope_id: str | None = Query(None),
    status: str | None = Query(
        None, description="'draft', 'active', 'retired', or 'unknown'"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: FhirProfileService = Depends(get_fhir_profile_service),
):
    total, rows = await service.list_profiles(
        resource_type, scope_level, scope_id, status, limit, offset
    )
    result = FhirProfileListResponse(
        total=total,
        limit=limit,
        offset=offset,
        data=[FhirProfileResponse.model_validate(r) for r in rows],
    )
    return JSONResponse(content=jsonable_encoder(result))


@router.get(
    "/{profile_id}",
    operation_id="get_fhir_profile",
    summary="Get a single FHIR profile by its database id",
    responses={**_SINGLE_200, 404: {"description": "Profile not found"}},
)
async def get_fhir_profile(
    profile_id: int,
    service: FhirProfileService = Depends(get_fhir_profile_service),
):
    profile = await service.get_profile(profile_id)
    return JSONResponse(
        content=jsonable_encoder(FhirProfileResponse.model_validate(profile))
    )


@router.patch(
    "/{profile_id}",
    operation_id="patch_fhir_profile",
    summary="Replace a draft profile's structure_definition",
    description=(
        "Only works while the profile is still status='draft' — 422 otherwise. "
        "Re-runs the same sidecar registration check create did."
    ),
    responses={
        **_SINGLE_200,
        404: {"description": "Profile not found"},
        422: {"description": "Not a draft, or the sidecar rejected the edit"},
    },
)
async def patch_fhir_profile(
    profile_id: int,
    body: FhirProfilePatchSchema,
    service: FhirProfileService = Depends(get_fhir_profile_service),
):
    profile = await service.update_draft_profile(
        profile_id, body.structure_definition, body.updated_by
    )
    return JSONResponse(
        content=jsonable_encoder(FhirProfileResponse.model_validate(profile))
    )


@router.post(
    "/{profile_id}/activate",
    operation_id="activate_fhir_profile",
    summary="Activate a draft profile, retiring whatever was active for the same scope",
    description=(
        "Atomically retires the previously-active row (if any) for this profile's "
        "own (resource_type, scope_level, scope_id) and activates this one, then "
        "evicts the matching fhir_profile_cache entry. A retired profile cannot be "
        "reactivated directly — create a new version instead."
    ),
    responses={
        **_SINGLE_200,
        404: {"description": "Profile not found"},
        422: {"description": "Profile is retired and cannot be reactivated directly"},
    },
)
async def activate_fhir_profile(
    profile_id: int,
    body: FhirProfileActivateSchema,
    service: FhirProfileService = Depends(get_fhir_profile_service),
):
    profile = await service.activate_profile(profile_id, body.updated_by)
    return JSONResponse(
        content=jsonable_encoder(FhirProfileResponse.model_validate(profile))
    )


@router.delete(
    "/{profile_id}",
    operation_id="delete_fhir_profile",
    summary="Delete a draft or retired profile",
    description="Refuses to delete a status='active' profile — activate a replacement first.",
    responses={
        204: {"description": "Deleted"},
        404: {"description": "Profile not found"},
        422: {"description": "Profile is active and cannot be deleted directly"},
    },
)
async def delete_fhir_profile(
    profile_id: int,
    service: FhirProfileService = Depends(get_fhir_profile_service),
):
    await service.delete_profile(profile_id)
    return Response(status_code=204)
