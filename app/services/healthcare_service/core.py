from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.fhir.mappers.healthcare_service import (
    to_fhir_healthcare_service,
    to_plain_healthcare_service,
)
from app.models.healthcare_service import HealthcareServiceModel
from app.repository.healthcare_service import HealthcareServiceRepository
from app.schemas.healthcare_service import (
    HealthcareServiceCreateSchema,
    HealthcareServicePatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All HealthcareService business logic. Like Organization, HealthcareService
    has no standalone sub-resource endpoints and no separate scalar-only vs.
    full create/patch split — see HealthcareServiceCreateSchema's docstring.
    Auth is identical to Organization's: org_id comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor."""

    def __init__(self, repository: HealthcareServiceRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, hs: HealthcareServiceModel) -> dict:
        return to_fhir_healthcare_service(hs)

    def _to_plain(self, hs: HealthcareServiceModel) -> dict:
        return to_plain_healthcare_service(hs)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_healthcare_service_scoped(
        self, healthcare_service_id: int, org_id: str | None
    ) -> HealthcareServiceModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "HealthcareService operation requires an org-scoped token"
            )
        hs = await self.repository.get_by_healthcare_service_id_in_org(
            healthcare_service_id, org_id
        )
        if not hs:
            raise NotFoundError("HealthcareService not found")
        return hs

    async def list_healthcare_services(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        name: str | None = None,
        identifier: str | None = None,
        category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        characteristic: str | None = None,
        program: str | None = None,
        provided_by: str | None = None,
        location: str | None = None,
        coverage_area: str | None = None,
        endpoint: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[HealthcareServiceModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_healthcare_service_scoped()."""
        if not org_id:
            raise PermissionDeniedError(
                "HealthcareService operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            active=active,
            name=name,
            identifier=identifier,
            category=category,
            service_type=service_type,
            specialty=specialty,
            characteristic=characteristic,
            program=program,
            provided_by=provided_by,
            location=location,
            coverage_area=coverage_area,
            endpoint=endpoint,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_healthcare_service(
        self,
        payload: HealthcareServiceCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> HealthcareServiceModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a HealthcareService at all."""
        if not org_id:
            raise PermissionDeniedError(
                "HealthcareService creation requires an org-scoped token"
            )
        hs = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "HealthcareService created",
            extra={
                "event": "healthcare_service.created",
                "healthcare_service_id": hs.healthcare_service_id,
            },
        )
        return hs

    async def patch_healthcare_service(
        self,
        healthcare_service_id: int,
        payload: HealthcareServicePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> HealthcareServiceModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a healthcare service belonging to a different org
        both raise NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id or not await self.repository.healthcare_service_belongs_to_org(
            healthcare_service_id, org_id
        ):
            self._log_org_scope_miss("patch", healthcare_service_id, org_id)
            raise NotFoundError("HealthcareService not found")
        updated = await self.repository.patch_full(
            healthcare_service_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("HealthcareService not found")
        logger.info(
            "HealthcareService updated",
            extra={
                "event": "healthcare_service.updated",
                "healthcare_service_id": healthcare_service_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_healthcare_service(
        self, healthcare_service_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_healthcare_service."""
        if not org_id or not await self.repository.healthcare_service_belongs_to_org(
            healthcare_service_id, org_id
        ):
            self._log_org_scope_miss("delete", healthcare_service_id, org_id)
            raise NotFoundError("HealthcareService not found")
        deleted = await self.repository.delete(healthcare_service_id)
        if not deleted:
            raise NotFoundError("HealthcareService not found")
        logger.info(
            "HealthcareService deleted",
            extra={
                "event": "healthcare_service.deleted",
                "healthcare_service_id": healthcare_service_id,
            },
        )

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, healthcare_service_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such healthcare service" — so
        this log line is the only place the distinction is recorded."""
        logger.warning(
            "HealthcareService write rejected by org scope",
            extra={
                "event": "healthcare_service.org_scope_miss",
                "operation": operation,
                "healthcare_service_id": healthcare_service_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
