from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.fhir.mappers.practitioner_role import (
    to_fhir_practitioner_role,
    to_plain_practitioner_role,
)
from app.models.practitioner_role import PractitionerRoleModel
from app.repository.practitioner_role import PractitionerRoleRepository
from app.schemas.practitioner_role import (
    PractitionerRoleCreateSchema,
    PractitionerRolePatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All PractitionerRole business logic. Like Organization/HealthcareService,
    PractitionerRole has no standalone sub-resource endpoints and no separate
    scalar-only vs. full create/patch split — see PractitionerRoleCreateSchema's
    docstring. Auth is identical to Organization's: org_id comes from the
    verified JWT's activeOrganizationId claim (actor.org_id), never a
    client-suppliable field, and there's no org-less/super-admin bypass —
    every operation requires an org-scoped actor."""

    def __init__(self, repository: PractitionerRoleRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, pr: PractitionerRoleModel) -> dict:
        return to_fhir_practitioner_role(pr)

    def _to_plain(self, pr: PractitionerRoleModel) -> dict:
        return to_plain_practitioner_role(pr)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_practitioner_role_scoped(
        self, practitioner_role_id: int, org_id: str | None
    ) -> PractitionerRoleModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "PractitionerRole operation requires an org-scoped token"
            )
        pr = await self.repository.get_by_practitioner_role_id_in_org(
            practitioner_role_id, org_id
        )
        if not pr:
            raise NotFoundError("PractitionerRole not found")
        return pr

    async def list_practitioner_roles(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        date: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        telecom: str | None = None,
        identifier: str | None = None,
        role: str | None = None,
        specialty: str | None = None,
        practitioner: str | None = None,
        organization: str | None = None,
        location: str | None = None,
        service: str | None = None,
        endpoint: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PractitionerRoleModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_practitioner_role_scoped()."""
        if not org_id:
            raise PermissionDeniedError(
                "PractitionerRole operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            active=active,
            date=date,
            email=email,
            phone=phone,
            telecom=telecom,
            identifier=identifier,
            role=role,
            specialty=specialty,
            practitioner=practitioner,
            organization=organization,
            location=location,
            service=service,
            endpoint=endpoint,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_practitioner_role(
        self,
        payload: PractitionerRoleCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> PractitionerRoleModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a PractitionerRole at all."""
        if not org_id:
            raise PermissionDeniedError(
                "PractitionerRole creation requires an org-scoped token"
            )
        pr = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "PractitionerRole created",
            extra={
                "event": "practitioner_role.created",
                "practitioner_role_id": pr.practitioner_role_id,
            },
        )
        return pr

    async def patch_practitioner_role(
        self,
        practitioner_role_id: int,
        payload: PractitionerRolePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> PractitionerRoleModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a practitioner role belonging to a different org
        both raise NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id or not await self.repository.practitioner_role_belongs_to_org(
            practitioner_role_id, org_id
        ):
            self._log_org_scope_miss("patch", practitioner_role_id, org_id)
            raise NotFoundError("PractitionerRole not found")
        updated = await self.repository.patch_full(
            practitioner_role_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("PractitionerRole not found")
        logger.info(
            "PractitionerRole updated",
            extra={
                "event": "practitioner_role.updated",
                "practitioner_role_id": practitioner_role_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_practitioner_role(
        self, practitioner_role_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_practitioner_role."""
        if not org_id or not await self.repository.practitioner_role_belongs_to_org(
            practitioner_role_id, org_id
        ):
            self._log_org_scope_miss("delete", practitioner_role_id, org_id)
            raise NotFoundError("PractitionerRole not found")
        deleted = await self.repository.delete(practitioner_role_id)
        if not deleted:
            raise NotFoundError("PractitionerRole not found")
        logger.info(
            "PractitionerRole deleted",
            extra={
                "event": "practitioner_role.deleted",
                "practitioner_role_id": practitioner_role_id,
            },
        )

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, practitioner_role_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such practitioner role" — so
        this log line is the only place the distinction is recorded."""
        logger.warning(
            "PractitionerRole write rejected by org scope",
            extra={
                "event": "practitioner_role.org_scope_miss",
                "operation": operation,
                "practitioner_role_id": practitioner_role_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
