from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.appointment import (
    AppointmentIdentifier,
    AppointmentModel,
    AppointmentParticipant,
    AppointmentServiceCategory,
    AppointmentServiceCategoryCoding,
    AppointmentServiceType,
    AppointmentServiceTypeCoding,
    AppointmentSlot,
    AppointmentSpecialty,
    AppointmentSpecialtyCoding,
    AppointmentStatus,
)

from ._shared import _parse_actor_ref, _parse_slot_ref, _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the Appointment parent row (no sub-resources)."""

    async def get_by_appointment_id(self, appointment_id: int) -> AppointmentModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AppointmentModel).where(AppointmentModel.appointment_id == appointment_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_appointment_id_in_org(
        self, appointment_id: int, org_id: str
    ) -> AppointmentModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the appointment exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AppointmentModel).where(
                    AppointmentModel.appointment_id == appointment_id,
                    AppointmentModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def appointment_belongs_to_org(self, appointment_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the appointment exists AND belongs
        to org_id."""
        async with self.session_factory() as session:
            stmt = select(AppointmentModel.id).where(
                AppointmentModel.appointment_id == appointment_id,
                AppointmentModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        status: AppointmentStatus | None = None,
        identifier: str | None = None,
        service_category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        actor: str | None = None,
        slot: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(AppointmentModel.tenant_id == org_id)
        stmt = apply_token_filter(stmt, AppointmentModel.status, status)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(AppointmentIdentifier.id).where(
                    AppointmentIdentifier.appointment_pk == AppointmentModel.id,
                    AppointmentIdentifier.value == identifier,
                ),
            )
        if service_category:
            stmt = apply_child_exists_filter(
                stmt,
                select(AppointmentServiceCategoryCoding.id)
                .join(
                    AppointmentServiceCategory,
                    AppointmentServiceCategoryCoding.appointment_service_category_id
                    == AppointmentServiceCategory.id,
                )
                .where(
                    AppointmentServiceCategory.appointment_pk == AppointmentModel.id,
                    AppointmentServiceCategoryCoding.code == service_category,
                ),
            )
        if service_type:
            stmt = apply_child_exists_filter(
                stmt,
                select(AppointmentServiceTypeCoding.id)
                .join(
                    AppointmentServiceType,
                    AppointmentServiceTypeCoding.appointment_service_type_id
                    == AppointmentServiceType.id,
                )
                .where(
                    AppointmentServiceType.appointment_pk == AppointmentModel.id,
                    AppointmentServiceTypeCoding.code == service_type,
                ),
            )
        if specialty:
            stmt = apply_child_exists_filter(
                stmt,
                select(AppointmentSpecialtyCoding.id)
                .join(
                    AppointmentSpecialty,
                    AppointmentSpecialtyCoding.appointment_specialty_id
                    == AppointmentSpecialty.id,
                )
                .where(
                    AppointmentSpecialty.appointment_pk == AppointmentModel.id,
                    AppointmentSpecialtyCoding.code == specialty,
                ),
            )
        if actor:
            a_type, a_id = _parse_actor_ref(actor)
            stmt = apply_child_exists_filter(
                stmt,
                select(AppointmentParticipant.id).where(
                    AppointmentParticipant.appointment_pk == AppointmentModel.id,
                    AppointmentParticipant.actor_type == a_type,
                    AppointmentParticipant.actor_id == a_id,
                ),
            )
        if slot:
            s_type, s_id = _parse_slot_ref(slot)
            stmt = apply_child_exists_filter(
                stmt,
                select(AppointmentSlot.id).where(
                    AppointmentSlot.appointment_pk == AppointmentModel.id,
                    AppointmentSlot.reference_type == s_type,
                    AppointmentSlot.reference_id == s_id,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: AppointmentStatus | None = None,
        identifier: str | None = None,
        service_category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        actor: str | None = None,
        slot: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[AppointmentModel], int | None]:
        """Paginated, filtered, sorted list of appointments. Returns
        (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "identifier": identifier,
                "service_category": service_category,
                "service_type": service_type,
                "specialty": specialty,
                "actor": actor,
                "slot": slot,
            }
            base = self._apply_list_filters(
                _with_relationships(select(AppointmentModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(AppointmentModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=AppointmentModel.appointment_id,
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
            "Appointments listed",
            extra={
                "event": "appointment.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    # ── Delete ────────────────────────────────────────────────────────────────
    # create()/patch() live in full.py — Appointment has no separate
    # scalar-only variant, see AppointmentCreateSchema's docstring.

    async def delete(self, appointment_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(AppointmentModel).where(
                AppointmentModel.appointment_id == appointment_id
            )
            appointment = (await session.execute(stmt)).scalars().first()
            if not appointment:
                return False
            try:
                await session.delete(appointment)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
