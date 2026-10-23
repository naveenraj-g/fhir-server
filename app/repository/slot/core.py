from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.slot import (
    SlotIdentifier,
    SlotModel,
    SlotServiceCategory,
    SlotServiceCategoryCoding,
    SlotServiceType,
    SlotServiceTypeCoding,
    SlotSpecialty,
    SlotSpecialtyCoding,
    SlotStatus,
)

from ._shared import _parse_schedule_ref, _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the Slot parent row (no sub-resources)."""

    async def get_by_slot_id(self, slot_id: int) -> SlotModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(SlotModel).where(SlotModel.slot_id == slot_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_slot_id_in_org(
        self, slot_id: int, org_id: str
    ) -> SlotModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the slot exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(SlotModel).where(
                    SlotModel.slot_id == slot_id,
                    SlotModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def slot_belongs_to_org(self, slot_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the slot exists AND belongs to
        org_id."""
        async with self.session_factory() as session:
            stmt = select(SlotModel.id).where(
                SlotModel.slot_id == slot_id,
                SlotModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        status: SlotStatus | None = None,
        identifier: str | None = None,
        service_category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        schedule: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(SlotModel.tenant_id == org_id)
        stmt = apply_token_filter(stmt, SlotModel.status, status)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(SlotIdentifier.id).where(
                    SlotIdentifier.slot_pk == SlotModel.id,
                    SlotIdentifier.value == identifier,
                ),
            )
        # service_category/service_type/specialty: each CodeableConcept's
        # coding is a real 0..* child table now — one EXISTS joining the
        # coding table to its parent row, correlated to the outer
        # SlotModel. Mirrors Schedule's own service_category filter.
        if service_category:
            stmt = apply_child_exists_filter(
                stmt,
                select(SlotServiceCategoryCoding.id)
                .join(
                    SlotServiceCategory,
                    SlotServiceCategoryCoding.slot_service_category_id
                    == SlotServiceCategory.id,
                )
                .where(
                    SlotServiceCategory.slot_pk == SlotModel.id,
                    SlotServiceCategoryCoding.code == service_category,
                ),
            )
        if service_type:
            stmt = apply_child_exists_filter(
                stmt,
                select(SlotServiceTypeCoding.id)
                .join(
                    SlotServiceType,
                    SlotServiceTypeCoding.slot_service_type_id == SlotServiceType.id,
                )
                .where(
                    SlotServiceType.slot_pk == SlotModel.id,
                    SlotServiceTypeCoding.code == service_type,
                ),
            )
        if specialty:
            stmt = apply_child_exists_filter(
                stmt,
                select(SlotSpecialtyCoding.id)
                .join(
                    SlotSpecialty,
                    SlotSpecialtyCoding.slot_specialty_id == SlotSpecialty.id,
                )
                .where(
                    SlotSpecialty.slot_pk == SlotModel.id,
                    SlotSpecialtyCoding.code == specialty,
                ),
            )
        if schedule:
            _, sch_id = _parse_schedule_ref(schedule)
            stmt = apply_token_filter(stmt, SlotModel.schedule_id, sch_id)
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: SlotStatus | None = None,
        identifier: str | None = None,
        service_category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        schedule: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[SlotModel], int | None]:
        """Paginated, filtered, sorted list of slots. Returns (rows,
        total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "identifier": identifier,
                "service_category": service_category,
                "service_type": service_type,
                "specialty": specialty,
                "schedule": schedule,
            }
            base = self._apply_list_filters(
                _with_relationships(select(SlotModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(SlotModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=SlotModel.slot_id,
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
            "Slots listed",
            extra={
                "event": "slot.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    # ── Delete ────────────────────────────────────────────────────────────────
    # create()/patch() live in full.py — Slot has no separate scalar-only
    # variant, see SlotCreateSchema's docstring.

    async def delete(self, slot_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(SlotModel).where(SlotModel.slot_id == slot_id)
            slot = (await session.execute(stmt)).scalars().first()
            if not slot:
                return False
            try:
                await session.delete(slot)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
