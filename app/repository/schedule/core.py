from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.schedule import (
    ScheduleActor,
    ScheduleIdentifier,
    ScheduleModel,
    ScheduleServiceCategory,
    ScheduleServiceType,
    ScheduleSpecialty,
)

from ._shared import _SORTABLE_FIELDS, _parse_actor_ref, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the Schedule parent row (no sub-resources)."""

    async def get_by_schedule_id(self, schedule_id: int) -> ScheduleModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ScheduleModel).where(ScheduleModel.schedule_id == schedule_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_schedule_id_in_org(
        self, schedule_id: int, org_id: str
    ) -> ScheduleModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the schedule exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ScheduleModel).where(
                    ScheduleModel.schedule_id == schedule_id,
                    ScheduleModel.org_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def schedule_belongs_to_org(self, schedule_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the schedule exists AND belongs to
        org_id."""
        async with self.session_factory() as session:
            stmt = select(ScheduleModel.id).where(
                ScheduleModel.schedule_id == schedule_id,
                ScheduleModel.org_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        active: bool | None = None,
        date: str | None = None,
        identifier: str | None = None,
        service_category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        actor: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(ScheduleModel.org_id == org_id)
        stmt = apply_token_filter(stmt, ScheduleModel.active, active)
        if date:
            stmt = stmt.where(
                (ScheduleModel.planning_horizon_start.is_(None))
                | (ScheduleModel.planning_horizon_start <= date),
                (ScheduleModel.planning_horizon_end.is_(None))
                | (ScheduleModel.planning_horizon_end >= date),
            )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(ScheduleIdentifier.id).where(
                    ScheduleIdentifier.schedule_id == ScheduleModel.id,
                    ScheduleIdentifier.value == identifier,
                ),
            )
        if service_category:
            stmt = apply_child_exists_filter(
                stmt,
                select(ScheduleServiceCategory.id).where(
                    ScheduleServiceCategory.schedule_id == ScheduleModel.id,
                    ScheduleServiceCategory.coding_code == service_category,
                ),
            )
        if service_type:
            stmt = apply_child_exists_filter(
                stmt,
                select(ScheduleServiceType.id).where(
                    ScheduleServiceType.schedule_id == ScheduleModel.id,
                    ScheduleServiceType.coding_code == service_type,
                ),
            )
        if specialty:
            stmt = apply_child_exists_filter(
                stmt,
                select(ScheduleSpecialty.id).where(
                    ScheduleSpecialty.schedule_id == ScheduleModel.id,
                    ScheduleSpecialty.coding_code == specialty,
                ),
            )
        if actor:
            actor_type, actor_id = _parse_actor_ref(actor)
            stmt = apply_child_exists_filter(
                stmt,
                select(ScheduleActor.id).where(
                    ScheduleActor.schedule_id == ScheduleModel.id,
                    ScheduleActor.reference_type == actor_type,
                    ScheduleActor.reference_id == actor_id,
                ),
            )
        return stmt

    async def list(
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
        """Paginated, filtered, sorted list of schedules. Returns (rows,
        total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "active": active,
                "date": date,
                "identifier": identifier,
                "service_category": service_category,
                "service_type": service_type,
                "specialty": specialty,
                "actor": actor,
            }
            base = self._apply_list_filters(
                _with_relationships(select(ScheduleModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(ScheduleModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=ScheduleModel.schedule_id,
                default_desc=True,
            )
            rows, total = await self._execute_paginated(
                session,
                base,
                count_base,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
        logger.debug(
            "Schedules listed",
            extra={
                "event": "schedule.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    # ── Delete ────────────────────────────────────────────────────────────────
    # create()/patch() live in full.py — Schedule has no separate scalar-only
    # variant, see ScheduleCreateSchema's docstring.

    async def delete(self, schedule_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(ScheduleModel).where(
                ScheduleModel.schedule_id == schedule_id
            )
            sched = (await session.execute(stmt)).scalars().first()
            if not sched:
                return False
            try:
                await session.delete(sched)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
