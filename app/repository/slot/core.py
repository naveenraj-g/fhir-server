from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.slot import SlotModel

from .search import slot_search

logger = get_logger(__name__)


class _CoreMixin:
    """Reads, search and delete. Every read loads only the slot row
    itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_slot_id(
        self, slot_id: int
    ) -> SlotModel | None:
        async with self.session_factory() as session:
            stmt = select(SlotModel).where(
                SlotModel.slot_id == slot_id
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_slot_id_in_org(
        self, slot_id: int, org_id: str
    ) -> SlotModel | None:
        """Lookup scoped to org_id — returns None unless the slot
        exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(SlotModel).where(
                SlotModel.slot_id == slot_id,
                SlotModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalars().first()

    async def slot_belongs_to_org(
        self, slot_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the slot exists AND belongs
        to org_id."""
        async with self.session_factory() as session:
            stmt = select(SlotModel.id).where(
                SlotModel.slot_id == slot_id,
                SlotModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    # ── Search ────────────────────────────────────────────────────────────
    # FHIR R4 search — every parameter, modifier and result parameter is
    # declared in search.py's registry and run by app.fhir.search.

    async def search(self, request: SearchRequest, ctx: SearchContext):
        """(matches for this page, total or None, included (type, row)
        pairs). Always scoped to ctx.tenant_id."""
        async with self.session_factory() as session:
            rows, total, included = await execute_search(
                session,
                model=SlotModel,
                registry=slot_search(),
                request=request,
                ctx=ctx,
                tiebreak=SlotModel.slot_id,
            )
        logger.debug(
            "Slots searched",
            extra={
                "event": "slot.searched",
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

    async def delete(self, slot_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(SlotModel).where(
                SlotModel.slot_id == slot_id
            )
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
