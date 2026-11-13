from app.core.config import settings
from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.input_payload import fhir_create_document, fhir_patch_fragment
from app.fhir.mappers.location import to_fhir_location
from app.fhir.search import SearchContext, SearchRequest, parse_search
from app.fhir.validation import validate_resource
from app.models.location import LocationModel
from app.repository.location import LocationRepository
from app.repository.location.search import location_search
from app.schemas.location import LocationCreateSchema, LocationPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Location business logic — shaped exactly like OrganizationService
    (Medplum-style storage: the FHIR body is validated and stored whole; see
    LocationModel's docstring). Auth matches
    Patient/Practitioner/Organization: org_id comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor."""

    def __init__(self, repository: LocationRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, loc: LocationModel) -> dict:
        return to_fhir_location(loc)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_location_scoped(
        self, location_id: int, org_id: str | None
    ) -> LocationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an unscoped
        lookup, then NotFoundError (404, never 403) if it belongs to a
        different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Location operation requires an org-scoped token"
            )
        loc = await self.repository.get_by_location_id_in_org(location_id, org_id)
        if not loc:
            raise NotFoundError("Location not found")
        return loc

    async def search_locations(
        self,
        query: list[tuple[str, str]],
        org_id: str | None,
        *,
        strict: bool = False,
        fhir_base: str | None = None,
    ) -> tuple[SearchRequest, list[LocationModel], int | None, list[tuple[str, object]]]:
        """FHIR R4 search. `query` is the raw (key, value) parameter list —
        parsed and validated here against the Location search registry
        (SearchError -> 400 OperationOutcome). `strict` is
        `Prefer: handling=strict`. Raises PermissionDeniedError (403) for an
        org-less token — same invariant as get_location_scoped().

        Returns (parsed request, matches, total, included (type, row) — an
        include can be another resource type, e.g. Organization)."""
        if not org_id:
            raise PermissionDeniedError("Location operation requires an org-scoped token")
        request = parse_search(
            query,
            location_search(),
            strict=strict,
            default_count=settings.pagination.default_limit,
            max_count=settings.pagination.max_limit,
        )
        ctx = SearchContext(tenant_id=org_id, fhir_base=fhir_base)
        rows, total, included = await self.repository.search(request, ctx)
        return request, rows, total, included

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_location(
        self,
        payload: LocationCreateSchema,
        org_id: str | None,
        created_by: str | None,
        body: dict | None = None,
    ) -> LocationModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Location at all.

        `body` is the raw request JSON, which is what base R4 validation
        checks and what is stored (see app.fhir.input_payload); falls back to
        the parsed payload for internal callers that have no raw body."""
        if not org_id:
            raise PermissionDeniedError(
                "Location creation requires an org-scoped token"
            )
        document = fhir_create_document(self._raw(payload, body), "Location")
        await self._validate_base_r4(document, org_id)
        loc = await self.repository.create_full(document, org_id, created_by)
        logger.info(
            "Location created",
            extra={"event": "location.created", "location_id": loc.location_id},
        )
        return loc

    async def patch_location(
        self,
        location_id: int,
        payload: LocationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
        body: dict | None = None,
    ) -> LocationModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a location belonging to a different org both raise
        NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        app.fhir.input_payload.fhir_patch_fragment()."""
        if not org_id:
            self._log_org_scope_miss("patch", location_id, org_id)
            raise NotFoundError("Location not found")
        existing = await self.repository.get_by_location_id_in_org(location_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", location_id, org_id)
            raise NotFoundError("Location not found")

        fragment, touched = fhir_patch_fragment(self._raw(payload, body))
        merged = merge_patch_fragment(to_fhir_location(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        # `merged` — the resource as it will look after this patch — is what
        # was just validated, and exactly what gets stored.
        updated = await self.repository.patch_full(location_id, merged, updated_by)
        if not updated:
            raise NotFoundError("Location not found")
        logger.info(
            "Location updated",
            extra={
                "event": "location.updated",
                "location_id": location_id,
                "fields": sorted(touched),
            },
        )
        return updated

    async def delete_location(
        self, location_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_location."""
        if not org_id or not await self.repository.location_belongs_to_org(
            location_id, org_id
        ):
            self._log_org_scope_miss("delete", location_id, org_id)
            raise NotFoundError("Location not found")
        deleted = await self.repository.delete(location_id)
        if not deleted:
            raise NotFoundError("Location not found")
        logger.info(
            "Location deleted",
            extra={"event": "location.deleted", "location_id": location_id},
        )

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    def _raw(payload, body: dict | None) -> dict:
        """The client's request JSON as sent; when there isn't one (an
        internal caller), the parsed payload's supplied fields instead."""
        if body is not None:
            return body
        return payload.model_dump(mode="json", exclude_unset=True)

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        """Raises FhirValidationError (422) if `fhir_resource` fails
        validation against the most specific applicable layer of the
        base -> country -> organization profile chain — see
        app.services.organization.core._CoreMixin._validate_base_r4's
        docstring for the full reasoning (identical here; validate_resource()
        is already resource-agnostic)."""
        errors = await validate_resource("Location", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Location failed base R4 validation",
                extra={"event": "location.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, location_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such location" — so this log
        line is the only place the distinction is recorded. Worth WARNING
        because a repeated cross-org miss is a very different signal from a
        typo'd id."""
        logger.warning(
            "Location write rejected by org scope",
            extra={
                "event": "location.org_scope_miss",
                "operation": operation,
                "location_id": location_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
