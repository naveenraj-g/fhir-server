from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.care_plan import get_care_plan_service
from app.schemas.care_plan import (
    CarePlanCreateSchema,
    CarePlanPatchSchema,
)
from app.services.care_plan import CarePlanService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
)

router = APIRouter()

logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_care_plan",
    summary="Create a new CarePlan resource",
    description=(
        "Describes the intention of how one or more practitioners intend to deliver care "
        "for a particular patient, group or community. "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_care_plan(
    payload: CarePlanCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_plan", "create")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    logger.info(
        "Create a new CarePlan resource",
        extra={"event": "route.create_care_plan"},
    )
    log_payload(logger, "care_plan.create.payload", payload)
    cp = await care_plan_service.create_care_plan(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        care_plan_service._to_fhir(cp),
        care_plan_service._to_plain(cp),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{care_plan_id}",
    operation_id="get_care_plan",
    summary="Get a CarePlan resource by ID",
    description=(
        "Returns the full CarePlan resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_care_plan(
    request: Request,
    care_plan_id: int = Path(
        ..., ge=1, description="Public care_plan identifier."
    ),
    actor: AuthUser = Depends(require_permission("care_plan", "read")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    logger.info(
        "Get a CarePlan resource by ID",
        extra={"event": "route.get_care_plan", "care_plan_id": care_plan_id},
    )
    cp = await care_plan_service.get_care_plan_scoped(
        care_plan_id, actor.org_id
    )
    return format_response(
        care_plan_service._to_fhir(cp),
        care_plan_service._to_plain(cp),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{care_plan_id}",
    operation_id="patch_care_plan",
    summary="Update a CarePlan resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_care_plan(
    payload: CarePlanPatchSchema,
    request: Request,
    care_plan_id: int = Path(
        ..., ge=1, description="Public care_plan identifier."
    ),
    actor: AuthUser = Depends(require_permission("care_plan", "update")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    logger.info(
        "Update a CarePlan resource",
        extra={
            "event": "route.patch_care_plan",
            "care_plan_id": care_plan_id,
        },
    )
    log_payload(logger, "care_plan.patch.payload", payload)
    updated = await care_plan_service.patch_care_plan(
        care_plan_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        care_plan_service._to_fhir(updated),
        care_plan_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_care_plans",
    summary="List all CarePlan resources",
    description=(
        "Returns a paginated list of CarePlan resources. Filter by status, "
        "intent, title, category, subject, encounter, author, based_on, replaces, "
        "part_of, addresses, goal, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_care_plans(
    request: Request,
    actor: AuthUser = Depends(require_permission("care_plan", "read")),
    status: str | None = Query(
        None, description="Status code (e.g. draft, active, completed)."
    ),
    intent: str | None = Query(
        None, description="Intent code (e.g. proposal, plan, order, option)."
    ),
    title: str | None = Query(None, description="Care plan title."),
    category: str | None = Query(None, description="Category code."),
    subject: str | None = Query(None, description="Subject reference (e.g. Patient/10001)."),
    encounter: str | None = Query(None, description="Encounter reference (e.g. Encounter/20001)."),
    author: str | None = Query(None, description="Author reference (e.g. Practitioner/30001)."),
    based_on: str | None = Query(None, description="basedOn reference."),
    replaces: str | None = Query(None, description="replaces reference."),
    part_of: str | None = Query(None, description="partOf reference."),
    addresses: str | None = Query(None, description="addresses reference (e.g. Condition/120001)."),
    goal: str | None = Query(None, description="goal reference."),
    identifier: str | None = Query(None, description="Business identifier value."),
    list_params: ListParams = Depends(),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    logger.info(
        "List CarePlan resources",
        extra={"event": "route.list_care_plans", "org_id": actor.org_id},
    )
    care_plans, total = await care_plan_service.list_care_plans(
        org_id=actor.org_id,
        status=status,
        intent=intent,
        title=title,
        category=category,
        subject=subject,
        encounter=encounter,
        author=author,
        based_on=based_on,
        replaces=replaces,
        part_of=part_of,
        addresses=addresses,
        goal=goal,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [care_plan_service._to_fhir(cp) for cp in care_plans],
        [care_plan_service._to_plain(cp) for cp in care_plans],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{care_plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_care_plan",
    summary="Delete a CarePlan resource",
    description=(
        "Permanently deletes the CarePlan and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_care_plan(
    care_plan_id: int = Path(
        ..., ge=1, description="Public care_plan identifier."
    ),
    actor: AuthUser = Depends(require_permission("care_plan", "delete")),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    logger.info(
        "Delete a CarePlan resource",
        extra={
            "event": "route.delete_care_plan",
            "care_plan_id": care_plan_id,
        },
    )
    await care_plan_service.delete_care_plan(
        care_plan_id, org_id=actor.org_id
    )
