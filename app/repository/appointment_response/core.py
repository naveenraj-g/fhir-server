from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.appointment_response import (
    AppointmentResponseIdentifier,
    AppointmentResponseModel,
    AppointmentResponseParticipantStatus,
)

from ._shared import (
    _parse_actor_ref,
    _parse_appointment_ref,
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the AppointmentResponse parent row (no sub-resources)."""

    async def get_by_appointment_response_id(
        self, appointment_response_id: int
    ) -> AppointmentResponseModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AppointmentResponseModel).where(
                    AppointmentResponseModel.appointment_response_id
                    == appointment_response_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_appointment_response_id_in_org(
        self, appointment_response_id: int, org_id: str
    ) -> AppointmentResponseModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the appointment response exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AppointmentResponseModel).where(
                    AppointmentResponseModel.appointment_response_id
                    == appointment_response_id,
                    AppointmentResponseModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def appointment_response_belongs_to_org(
        self, appointment_response_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the row exists AND belongs to
        org_id."""
        async with self.session_factory() as session:
            stmt = select(AppointmentResponseModel.id).where(
                AppointmentResponseModel.appointment_response_id
                == appointment_response_id,
                AppointmentResponseModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        identifier: str | None = None,
        appointment: str | None = None,
        actor: str | None = None,
        part_status: AppointmentResponseParticipantStatus | None = None,
    ):
        if org_id:
            stmt = stmt.where(AppointmentResponseModel.tenant_id == org_id)
        stmt = apply_token_filter(
            stmt, AppointmentResponseModel.participant_status, part_status
        )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(AppointmentResponseIdentifier.id).where(
                    AppointmentResponseIdentifier.appointment_response_pk
                    == AppointmentResponseModel.id,
                    AppointmentResponseIdentifier.value == identifier,
                ),
            )
        if appointment:
            a_type, a_id = _parse_appointment_ref(appointment)
            stmt = stmt.where(
                AppointmentResponseModel.appointment_type == a_type,
                AppointmentResponseModel.appointment_id == a_id,
            )
        if actor:
            act_type, act_id = _parse_actor_ref(actor)
            stmt = stmt.where(
                AppointmentResponseModel.actor_type == act_type,
                AppointmentResponseModel.actor_id == act_id,
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        identifier: str | None = None,
        appointment: str | None = None,
        actor: str | None = None,
        part_status: AppointmentResponseParticipantStatus | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[AppointmentResponseModel], int | None]:
        """Paginated, filtered, sorted list of appointment responses.
        Returns (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "identifier": identifier,
                "appointment": appointment,
                "actor": actor,
                "part_status": part_status,
            }
            base = self._apply_list_filters(
                _with_relationships(select(AppointmentResponseModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(AppointmentResponseModel),
                **filter_kwargs,
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=AppointmentResponseModel.appointment_response_id,
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
            "AppointmentResponses listed",
            extra={
                "event": "appointment_response.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    # ── Delete ────────────────────────────────────────────────────────────────
    # create()/patch() live in full.py — AppointmentResponse has no
    # separate scalar-only variant, see AppointmentResponseCreateSchema's
    # docstring.

    async def delete(self, appointment_response_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(AppointmentResponseModel).where(
                AppointmentResponseModel.appointment_response_id
                == appointment_response_id
            )
            row = (await session.execute(stmt)).scalars().first()
            if not row:
                return False
            try:
                await session.delete(row)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
