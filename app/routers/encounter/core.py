from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.encounter import get_encounter_service
from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema
from app.schemas.enums import EncounterStatus
from app.services.encounter import EncounterService

from ._responses import _CONTENT_NEG, _ERR_NOT_FOUND, _ERR_VALIDATION, _LIST_200, _SINGLE_200, _SINGLE_201

router = APIRouter()

logger = get_logger(__name__)

_FHIR_REFERENCE_PATTERN = r"^[A-Za-z]+/[0-9]+$"


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_encounter",
    summary="Create a new Encounter resource",
    description=(
        "An interaction between a patient and healthcare provider(s) for the purpose "
        "of providing healthcare service(s) or assessing the health status of a "
        "patient. Encounter is set once and then patched rather than built up "
        "incrementally, so this single endpoint accepts the full nested payload — "
        "identifier, statusHistory, classHistory, type, episodeOfCare, basedOn, "
        "appointment, reasonCode, reasonReference, account, participant, diagnosis, "
        "hospitalization, and location — atomically in one DB transaction. `status` "
        "and `class_coding` are required. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_encounter(
    payload: EncounterCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("encounter", "create")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub). Encounter has no user_id field at all."""
    logger.info("Create a new Encounter resource", extra={"event": "route.create_encounter"})
    log_payload(logger, "encounter.create.payload", payload)
    encounter = await encounter_service.create_encounter(payload, actor.org_id, actor.sub)
    return format_response(
        encounter_service._to_fhir(encounter),
        encounter_service._to_plain(encounter),
        request,
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/{encounter_id}",
    operation_id="get_encounter_by_id",
    summary="Retrieve an Encounter resource by public encounter_id",
    description=(
        "Scoped to the caller's own org — get_encounter_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_encounter(
    request: Request,
    encounter_id: int = Path(..., ge=1, description="Public encounter identifier."),
    actor: AuthUser = Depends(require_permission("encounter", "read")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    logger.info(
        "Retrieve an Encounter resource by public encounter_id",
        extra={"event": "route.get_encounter_by_id", "encounter_id": encounter_id},
    )
    encounter = await encounter_service.get_encounter_scoped(encounter_id, actor.org_id)
    return format_response(encounter_service._to_fhir(encounter), encounter_service._to_plain(encounter), request)


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{encounter_id}",
    operation_id="patch_encounter",
    summary="Update an Encounter resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (even `[]`) atomically replaces the corresponding "
        "rows; omitted lists are left untouched. `hospitalization` is 0..1 — supplying "
        "it replaces the whole block, supplying `null` clears it. "
        "Scoped to the caller's own org — patch_encounter() raises NotFoundError "
        "(404, not 403) if actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_encounter(
    payload: EncounterPatchSchema,
    request: Request,
    encounter_id: int = Path(..., ge=1, description="Public encounter identifier."),
    actor: AuthUser = Depends(require_permission("encounter", "update")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    """updated_by comes from the verified JWT (actor.sub)."""
    logger.info("Update an Encounter resource", extra={"event": "route.patch_encounter", "encounter_id": encounter_id})
    log_payload(logger, "encounter.patch.payload", payload)
    updated = await encounter_service.patch_encounter(encounter_id, payload, actor.sub, org_id=actor.org_id)
    return format_response(encounter_service._to_fhir(updated), encounter_service._to_plain(updated), request)


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_encounters",
    summary="List all Encounter resources",
    description=(
        "Returns a paginated list of Encounter resources, matching a subset of the "
        "search parameter set documented at "
        "https://www.hl7.org/fhir/R4/encounter.html#search. "
        "Filter by `status`, `identifier` (exact business-identifier value), "
        "`subject` (FHIR reference string), `class` (exact code match), `type` "
        "(exact code match), `service-provider` (FHIR reference string), `part-of` "
        "(FHIR reference string). Always scoped to the caller's own org. "
        "Sort with `sort` (e.g. `-period_start`); set `total_mode=none` to skip the "
        "COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_encounters(
    request: Request,
    actor: AuthUser = Depends(require_permission("encounter", "read")),
    encounter_status: EncounterStatus | None = Query(
        None,
        alias="status",
        description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown.",
    ),
    identifier: str | None = Query(None, description="Exact match on a business identifier value."),
    subject: str | None = Query(None, pattern=_FHIR_REFERENCE_PATTERN, description="FHIR reference string, e.g. `Patient/999`."),
    class_code: str | None = Query(None, alias="class", description="Exact match on the Encounter.class code."),
    type_code: str | None = Query(None, alias="type", description="Exact match on a coded Encounter.type."),
    service_provider: str | None = Query(None, alias="service-provider", pattern=_FHIR_REFERENCE_PATTERN, description="FHIR reference string, e.g. `Organization/190001`."),
    part_of: str | None = Query(None, alias="part-of", pattern=_FHIR_REFERENCE_PATTERN, description="FHIR reference string, e.g. `Encounter/20001`."),
    params: ListParams = Depends(),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    logger.info("List all Encounter resources", extra={"event": "route.list_encounters"})
    items, total = await encounter_service.list_encounters(
        org_id=actor.org_id,
        status=encounter_status,
        identifier=identifier,
        subject=subject,
        class_code=class_code,
        type_code=type_code,
        service_provider=service_provider,
        part_of=part_of,
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return format_paginated_response(
        [encounter_service._to_fhir(e) for e in items],
        [encounter_service._to_plain(e) for e in items],
        total,
        params.limit,
        params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{encounter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_encounter",
    summary="Delete an Encounter resource",
    description=(
        "Permanently deletes the Encounter and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "encounter exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_encounter(
    encounter_id: int = Path(..., ge=1, description="Public encounter identifier."),
    actor: AuthUser = Depends(require_permission("encounter", "delete")),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    logger.info("Delete an Encounter resource", extra={"event": "route.delete_encounter", "encounter_id": encounter_id})
    await encounter_service.delete_encounter(encounter_id, org_id=actor.org_id)
