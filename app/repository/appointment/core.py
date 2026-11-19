from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.appointment import AppointmentModel

from .search import appointment_search

logger = get_logger(__name__)


class _CoreMixin:
    """Reads, search and delete. Every read loads only the appointment row
    itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_appointment_id(self, appointment_id: int) -> AppointmentModel | None:
        async with self.session_factory() as session:
            stmt = select(AppointmentModel).where(AppointmentModel.appointment_id == appointment_id)
            return (await session.execute(stmt)).scalars().first()

    async def get_by_appointment_id_in_org(self, appointment_id: int, org_id: str) -> AppointmentModel | None:
        """Lookup scoped to org_id — returns None unless the appointment
        exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(AppointmentModel).where(
                AppointmentModel.appointment_id == appointment_id,
                AppointmentModel.tenant_id == org_id,
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
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    # ── Search ────────────────────────────────────────────────────────────
    # FHIR R4 search — every parameter, modifier and result parameter is
    # declared in search.py's registry and run by app.fhir.search.

    async def search(self, request: SearchRequest, ctx: SearchContext):
        """(matches for this page, total or None, included (type, row)
        pairs). Always scoped to ctx.tenant_id."""
        async with self.session_factory() as session:
            rows, total, included = await execute_search(
                session,
                model=AppointmentModel,
                registry=appointment_search(),
                request=request,
                ctx=ctx,
                tiebreak=AppointmentModel.appointment_id,
            )
        logger.debug(
            "Appointments searched",
            extra={
                "event": "appointment.searched",
                "returned": len(rows),
                "included": len(included),
                "total": total,
                "count": request.count,
                "offset": request.offset,
                "params": sorted({c.key for c in request.clauses}),
            },
        )
        return rows, total, included

    # ── Delete ────────────────────────────────────────────────────────────────
    # create_full()/patch_full() live in full.py.

    async def delete(self, appointment_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(AppointmentModel).where(AppointmentModel.appointment_id == appointment_id)
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
