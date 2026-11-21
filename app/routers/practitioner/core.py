from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.config import settings
from app.core.content_negotiation import (
    FHIRJSONResponse,
    fhir_response,
    require_fhir_json,
)
from app.core.logging import get_logger, log_payload
from app.core.schema_utils import inline_schema
from app.di.dependencies.practitioner import get_practitioner_service
from app.fhir.search.openapi import search_description, search_parameters
from app.repository.practitioner.search import practitioner_search
from app.routers._fhir_search import (
    get_query,
    post_query,
    search_urls,
    searchset_response,
    strict_handling,
)
from app.schemas.practitioner import (
    PractitionerCreateSchema,
    PractitionerPatchSchema,
    PractitionerUserLinkInput,
    PractitionerUserLinkResponse,
)
from app.services.practitioner import PractitionerService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_ACCEPTABLE,
    _ERR_NOT_FOUND,
    _ERR_SEARCH,
    _ERR_VALIDATION,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
)

# Practitioner always responds with FHIR R4 JSON, whatever the Accept
# header says (Medplum's approach) — only a client that rules JSON out
# entirely (Accept: application/fhir+xml, _format=xml) gets a 406.
router = APIRouter(
    default_response_class=FHIRJSONResponse,
    dependencies=[Depends(require_fhir_json)],
    responses={**_ERR_NOT_ACCEPTABLE},
)

logger = get_logger(__name__)

# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_practitioner",
    summary="Create a new Practitioner resource",
    description=(
        "Records a person with a formal responsibility in providing healthcare or related "
        "services. The request body is a FHIR R4 Practitioner resource (camelCase, nested "
        "datatypes — https://www.hl7.org/fhir/R4/practitioner.html); the practitioner and every "
        "supplied element (identifier, name, telecom, address, photo, qualification, "
        "communication) are written atomically in one DB transaction. The body is checked "
        "against base FHIR R4: any valid R4 element is accepted and stored as sent "
        "(server-managed `id`/`meta` are ignored); a key that isn't FHIR at all is rejected with "
        "422. A qualification's `issuer` may reference an Organization "
        '(e.g. `{"reference": "Organization/190001"}`) — rejected with 422 if it doesn\'t exist. '
        "The record starts unlinked: the end-user it belongs to (what `GET /me` scopes to) is "
        "linked afterwards with `PUT /{practitioner_id}/user`. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_practitioner(
    payload: PractitionerCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """org_id and created_by both come from the verified JWT (actor.org_id /
    actor.sub) — org_id is not a request body field at all, and an org-less
    token is rejected outright (403). Create never links an end-user (see
    link_practitioner_user)."""
    logger.info(
        "Create a new Practitioner resource",
        extra={"event": "route.create_practitioner"},
    )
    log_payload(logger, "practitioner.create.payload", payload)
    practitioner = await practitioner_service.create_practitioner(
        payload, actor.org_id, actor.sub, body=await request.json()
    )
    return fhir_response(
        practitioner_service._to_fhir(practitioner),
        status_code=status.HTTP_201_CREATED,
    )


# ── Search ─────────────────────────────────────────────────────────────────
# FHIR R4 search (https://www.hl7.org/fhir/R4/search.html). Query
# parameters are read raw from the request — FHIR parameter names carry
# modifiers (`name:exact`), chains and repeat for AND, none of which fit
# FastAPI's per-name Query() declarations — and validated against the
# Practitioner search registry. The OpenAPI parameter list is generated
# from that same registry.

_SEARCH_REGISTRY = practitioner_search()
_SEARCH_PARAMETERS = search_parameters(
    _SEARCH_REGISTRY, settings.pagination.max_limit, settings.pagination.default_limit
)
_SEARCH_DESCRIPTION = (
    search_description(_SEARCH_REGISTRY)
    + " Always scoped to the caller's own org (from the verified token) — `org_id` is not a "
    "client-suppliable filter. " + _CONTENT_NEG
)
_FORM_BODY = {
    "required": False,
    "content": {
        "application/x-www-form-urlencoded": {
            "schema": {
                "type": "object",
                "properties": {
                    p["name"]: {**p["schema"], "description": p["description"]}
                    for p in _SEARCH_PARAMETERS
                    if p["in"] == "query"
                },
            }
        }
    },
}


async def _search(
    request: Request,
    query: list[tuple[str, str]],
    actor: AuthUser,
    practitioner_service: PractitionerService,
    route_name: str,
    user_id: str | None = None,
):
    # fhir_base always comes from the main search route (`/me` sits one
    # segment deeper); the paging links point back at the route that ran.
    _, fhir_base = search_urls(request, "search_practitioners")
    search_url = str(request.url_for(route_name))
    (
        search_request,
        rows,
        total,
        included,
    ) = await practitioner_service.search_practitioners(
        query,
        actor.org_id,
        strict=strict_handling(request),
        fhir_base=fhir_base,
        user_id=user_id,
    )
    return searchset_response(
        registry=_SEARCH_REGISTRY,
        search_request=search_request,
        search_url=search_url,
        fhir_base=fhir_base,
        rows=rows,
        total=total,
        included=included,
    )


@router.get(
    "/",
    operation_id="search_practitioners",
    summary="Search Practitioner resources (FHIR R4 search)",
    description=_SEARCH_DESCRIPTION,
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_practitioners(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """org_id is always the caller's own (actor.org_id), never
    client-suppliable; an org-less token is rejected outright (403)."""
    logger.info(
        "Search Practitioner resources",
        extra={"event": "route.search_practitioners"},
    )
    return await _search(
        request, get_query(request), actor, practitioner_service, "search_practitioners"
    )


@router.post(
    "/_search",
    operation_id="search_practitioners_post",
    summary="Search Practitioner resources (FHIR R4 search via POST)",
    description=(
        "Same search as `GET /`, with the parameters sent as an "
        "`application/x-www-form-urlencoded` body (R4 `POST [base]/[type]/_search`) — use it when "
        "the query string would be too long, or to keep search values out of URLs. Query-string "
        "parameters, if any, are combined with the body. " + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS, "requestBody": _FORM_BODY},
)
async def search_practitioners_post(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Search Practitioner resources (POST _search)",
        extra={"event": "route.search_practitioners_post"},
    )
    return await _search(
        request,
        await post_query(request),
        actor,
        practitioner_service,
        "search_practitioners",
    )


# ── Me (must come before /{practitioner_id}) ────────────────────────────


@router.get(
    "/me",
    operation_id="search_my_practitioners",
    summary="Search Practitioner resources owned by the authenticated end-user",
    description=(
        "Same search as `GET /` (every parameter, modifier and result parameter), always "
        "additionally restricted to the authenticated end-user's own records — those linked "
        "to the token's `sub` (see `PUT /{practitioner_id}/user`) — on top of the caller's own org. "
        + _SEARCH_DESCRIPTION
    ),
    responses={**_LIST_200, **_ERR_SEARCH},
    openapi_extra={"parameters": _SEARCH_PARAMETERS},
)
async def search_my_practitioners(
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Search Practitioner resources owned by the authenticated end-user",
        extra={"event": "route.search_my_practitioners"},
    )
    return await _search(
        request,
        get_query(request),
        actor,
        practitioner_service,
        "search_my_practitioners",
        user_id=actor.sub,
    )


# ── Get ──────────────────────────────────────────────────────────────────


@router.get(
    "/{practitioner_id}",
    operation_id="get_practitioner_by_id",
    summary="Retrieve a Practitioner resource by public practitioner_id",
    description=(
        "Scoped to the caller's own org — get_practitioner_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_practitioner(
    request: Request,
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Retrieve a Practitioner resource by public practitioner_id",
        extra={
            "event": "route.get_practitioner_by_id",
            "practitioner_id": practitioner_id,
        },
    )
    practitioner = await practitioner_service.get_practitioner_scoped(
        practitioner_id, actor.org_id
    )
    return fhir_response(practitioner_service._to_fhir(practitioner))


# ── Patch ────────────────────────────────────────────────────────────────


@router.patch(
    "/{practitioner_id}",
    operation_id="patch_practitioner",
    summary="Update a Practitioner resource",
    description=(
        "The request body is a partial FHIR R4 Practitioner (merge-patch on top-level elements). "
        "Only supplied elements are written; omitted elements are left unchanged. Every supplied "
        "list (identifier, name, telecom, address, photo, qualification, communication — even "
        "`[]`) atomically replaces the stored entries, and `null` clears an element. "
        "Scoped to the caller's own org — patch_practitioner() raises NotFoundError (404, not "
        "403 — avoids leaking that a practitioner with this id exists in another org) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner(
    payload: PractitionerPatchSchema,
    request: Request,
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """updated_by comes from the verified JWT (actor.sub); patch_practitioner()
    raises NotFoundError (404, not 403) if actor.org_id doesn't match."""
    logger.info(
        "Update a Practitioner resource",
        extra={"event": "route.patch_practitioner", "practitioner_id": practitioner_id},
    )
    log_payload(logger, "practitioner.patch.payload", payload)
    updated = await practitioner_service.patch_practitioner(
        practitioner_id,
        payload,
        actor.sub,
        org_id=actor.org_id,
        body=await request.json(),
    )
    return fhir_response(practitioner_service._to_fhir(updated))


# ── End-user link ────────────────────────────────────────────────────────
# Which IAM user acts as this practitioner. Not a FHIR element, so it is
# not in the resource body and not settable through create/patch — only
# here, behind its own permission (the equivalent of creating a Medplum
# ProjectMembership with `profile` = this practitioner).

_USER_LINK_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PractitionerUserLinkResponse.model_json_schema()
                )
            }
        }
    }
}


def _link_response(practitioner) -> JSONResponse:
    return JSONResponse(
        PractitionerUserLinkResponse(
            practitioner_id=practitioner.practitioner_id, user_id=practitioner.user_id
        ).model_dump()
    )


@router.get(
    "/{practitioner_id}/user",
    operation_id="get_practitioner_user_link",
    summary="Show which end-user is linked to a Practitioner",
    description=(
        "Returns the linked IAM user id, or `null` when the record is not linked. Not a FHIR "
        "resource (`application/json`). Scoped to the caller's own org like every other read."
    ),
    responses={**_USER_LINK_200, **_ERR_NOT_FOUND},
    response_class=JSONResponse,
)
async def get_practitioner_user_link(
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Get a Practitioner end-user link",
        extra={
            "event": "route.get_practitioner_user_link",
            "practitioner_id": practitioner_id,
        },
    )
    return _link_response(
        await practitioner_service.get_user_link(practitioner_id, actor.org_id)
    )


@router.put(
    "/{practitioner_id}/user",
    operation_id="link_practitioner_user",
    summary="Link an end-user to a Practitioner",
    description=(
        "Links the IAM user `user_id` (a JWT `sub`) to this practitioner, so that user's "
        "`GET /me` returns it. Replaces any previous link; linking the same user again is a "
        "no-op. A user can act as at most one practitioner per org (422 if already linked "
        "to another). Requires the separate `practitioner:link` permission — linking is how "
        "an onboarding/verification flow (or an admin) confirms that a person is this "
        "practitioner. Scoped to the caller's own org (404 across orgs)."
    ),
    responses={**_USER_LINK_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    response_class=JSONResponse,
)
async def link_practitioner_user(
    payload: PractitionerUserLinkInput,
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "link")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Link an end-user to a Practitioner",
        extra={
            "event": "route.link_practitioner_user",
            "practitioner_id": practitioner_id,
        },
    )
    return _link_response(
        await practitioner_service.link_user(
            practitioner_id, payload.user_id, actor.org_id, actor.sub
        )
    )


@router.delete(
    "/{practitioner_id}/user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="unlink_practitioner_user",
    summary="Remove the end-user link from a Practitioner",
    description=(
        "Clears the link; idempotent (204 whether or not it was linked). The Practitioner "
        "record itself is untouched. Requires `practitioner:link`. Scoped to the caller's own "
        "org (404 across orgs)."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def unlink_practitioner_user(
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "link")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    logger.info(
        "Remove a Practitioner end-user link",
        extra={
            "event": "route.unlink_practitioner_user",
            "practitioner_id": practitioner_id,
        },
    )
    await practitioner_service.unlink_user(practitioner_id, actor.org_id, actor.sub)


# ── Delete ───────────────────────────────────────────────────────────────


@router.delete(
    "/{practitioner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner",
    summary="Delete a Practitioner resource",
    description=(
        "Permanently deletes the Practitioner and its search-index rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "practitioner exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_practitioner(
    practitioner_id: int = Path(
        ..., ge=1, description="Public practitioner identifier."
    ),
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    """delete_practitioner() raises NotFoundError (404) if the id doesn't
    exist at all, or if it exists but belongs to a different org."""
    logger.info(
        "Delete a Practitioner resource",
        extra={
            "event": "route.delete_practitioner",
            "practitioner_id": practitioner_id,
        },
    )
    await practitioner_service.delete_practitioner(practitioner_id, org_id=actor.org_id)
