from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.care_plan import CarePlanModel

from .search import care_plan_search

logger = get_logger(__name__)

_M = CarePlanModel


class _CoreMixin:
    """Reads, search and delete. Every read loads only the care_plan
    row itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_care_plan_id(self, care_plan_id: int) -> _M | None:
        async with self.session_factory() as session:
            stmt = select(_M).where(_M.care_plan_id == care_plan_id)
            return (await session.execute(stmt)).scalars().first()

    async def get_by_care_plan_id_in_org(
        self, care_plan_id: int, org_id: str
    ) -> _M | None:
        """Lookup scoped to org_id — returns None unless the care_plan
        exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(_M).where(
                _M.care_plan_id == care_plan_id, _M.tenant_id == org_id
            )
            return (await session.execute(stmt)).scalars().first()

    async def care_plan_belongs_to_org(self, care_plan_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the care_plan exists AND
        belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(_M.id).where(
                _M.care_plan_id == care_plan_id, _M.tenant_id == org_id
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
                model=_M,
                registry=care_plan_search(),
                request=request,
                ctx=ctx,
                tiebreak=_M.care_plan_id,
            )
        logger.debug(
            "CarePlans searched",
            extra={
                "event": "care_plan.searched",
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

    async def delete(self, care_plan_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(_M).where(_M.care_plan_id == care_plan_id)
            care_plan = (await session.execute(stmt)).scalars().first()
            if not care_plan:
                return False
            try:
                await session.delete(care_plan)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
