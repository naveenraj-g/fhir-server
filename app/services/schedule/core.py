from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.fhir.mappers.schedule import to_fhir_schedule, to_plain_schedule
from app.models.schedule import ScheduleModel
from app.repository.schedule import ScheduleRepository
from app.schemas.schedule import ScheduleCreateSchema, SchedulePatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Schedule business logic. Like Organization/HealthcareService,
    Schedule has no standalone sub-resource endpoints and no separate
    scalar-only vs. full create/patch split — see ScheduleCreateSchema's
    docstring. Auth is identical to HealthcareService's: org_id comes from
    the verified JWT's activeOrganizationId claim (actor.org_id), never a
    client-suppliable field, and there's no org-less/super-admin bypass —
    every operation requires an org-scoped actor."""

    def __init__(self, repository: ScheduleRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, sched: ScheduleModel) -> dict:
        return to_fhir_schedule(sched)

    def _to_plain(self, sched: ScheduleModel) -> dict:
        return to_plain_schedule(sched)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_schedule_scoped(
        self, schedule_id: int, org_id: str | None
    ) -> ScheduleModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Schedule operation requires an org-scoped token"
            )
        sched = await self.repository.get_by_schedule_id_in_org(schedule_id, org_id)
        if not sched:
            raise NotFoundError("Schedule not found")
        return sched

    async def list_schedules(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        date: str | None = None,
        identifier: str | None = None,
        service_category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        actor: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ScheduleModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_schedule_scoped()."""
        if not org_id:
            raise PermissionDeniedError(
                "Schedule operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            active=active,
            date=date,
            identifier=identifier,
            service_category=service_category,
            service_type=service_type,
            specialty=specialty,
            actor=actor,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_schedule(
        self,
        payload: ScheduleCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ScheduleModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Schedule at all."""
        if not org_id:
            raise PermissionDeniedError("Schedule creation requires an org-scoped token")
        sched = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Schedule created",
            extra={"event": "schedule.created", "schedule_id": sched.schedule_id},
        )
        return sched

    async def patch_schedule(
        self,
        schedule_id: int,
        payload: SchedulePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ScheduleModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a schedule belonging to a different org both raise
        NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id or not await self.repository.schedule_belongs_to_org(
            schedule_id, org_id
        ):
            self._log_org_scope_miss("patch", schedule_id, org_id)
            raise NotFoundError("Schedule not found")
        updated = await self.repository.patch_full(schedule_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Schedule not found")
        logger.info(
            "Schedule updated",
            extra={
                "event": "schedule.updated",
                "schedule_id": schedule_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_schedule(
        self, schedule_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_schedule."""
        if not org_id or not await self.repository.schedule_belongs_to_org(
            schedule_id, org_id
        ):
            self._log_org_scope_miss("delete", schedule_id, org_id)
            raise NotFoundError("Schedule not found")
        deleted = await self.repository.delete(schedule_id)
        if not deleted:
            raise NotFoundError("Schedule not found")
        logger.info(
            "Schedule deleted",
            extra={"event": "schedule.deleted", "schedule_id": schedule_id},
        )

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, schedule_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such schedule" — so this log
        line is the only place the distinction is recorded."""
        logger.warning(
            "Schedule write rejected by org scope",
            extra={
                "event": "schedule.org_scope_miss",
                "operation": operation,
                "schedule_id": schedule_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
