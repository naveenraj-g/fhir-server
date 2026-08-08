from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.fhir.mappers.location import to_fhir_location, to_plain_location
from app.models.location import LocationModel
from app.repository.location import LocationRepository
from app.schemas.location import LocationCreateSchema, LocationPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Location business logic. Shaped exactly like OrganizationService:
    no standalone sub-resource endpoints and no separate scalar-only vs. full
    create/patch split — see LocationCreateSchema's docstring. Auth matches
    Patient/Practitioner/Organization: org_id comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor."""

    def __init__(self, repository: LocationRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, loc: LocationModel) -> dict:
        return to_fhir_location(loc)

    def _to_plain(self, loc: LocationModel) -> dict:
        return to_plain_location(loc)

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

    async def list_locations(
        self,
        org_id: str | None = None,
        name: str | None = None,
        identifier: str | None = None,
        location_status=None,
        operational_status: str | None = None,
        location_type: str | None = None,
        physical_type: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        organization: str | None = None,
        partof: str | None = None,
        endpoint: str | None = None,
        near: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[LocationModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_location_scoped()."""
        if not org_id:
            raise PermissionDeniedError(
                "Location operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            name=name,
            identifier=identifier,
            location_status=location_status,
            operational_status=operational_status,
            location_type=location_type,
            physical_type=physical_type,
            address=address,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            address_country=address_country,
            address_use=address_use,
            organization=organization,
            partof=partof,
            endpoint=endpoint,
            near=near,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_location(
        self,
        payload: LocationCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> LocationModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Location at all."""
        if not org_id:
            raise PermissionDeniedError(
                "Location creation requires an org-scoped token"
            )
        loc = await self.repository.create_full(payload, org_id, created_by)
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
    ) -> LocationModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a location belonging to a different org both raise
        NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id or not await self.repository.location_belongs_to_org(
            location_id, org_id
        ):
            self._log_org_scope_miss("patch", location_id, org_id)
            raise NotFoundError("Location not found")
        updated = await self.repository.patch_full(location_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Location not found")
        logger.info(
            "Location updated",
            extra={
                "event": "location.updated",
                "location_id": location_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
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
