from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.location import LocationModel

from .search import location_search

logger = get_logger(__name__)


class _CoreMixin:
    """Reads, search and delete. Every read loads only the location row
    itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_location_id(self, location_id: int) -> LocationModel | None:
        async with self.session_factory() as session:
            stmt = select(LocationModel).where(LocationModel.location_id == location_id)
            return (await session.execute(stmt)).scalars().first()

    async def get_by_location_id_in_org(
        self, location_id: int, org_id: str
    ) -> LocationModel | None:
        """Lookup scoped to org_id — returns None unless the location exists
        AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(LocationModel).where(
                LocationModel.location_id == location_id,
                LocationModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalars().first()

    async def location_belongs_to_org(self, location_id: int, org_id: str) -> bool:
        """Lightweight existence check for tenant-ownership gates on write
        routes — True iff the location exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(LocationModel.id).where(
                LocationModel.location_id == location_id,
                LocationModel.tenant_id == org_id,
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
                model=LocationModel,
                registry=location_search(),
                request=request,
                ctx=ctx,
                tiebreak=LocationModel.location_id,
            )
        logger.debug(
            "Locations searched",
            extra={
                "event": "location.searched",
                "returned": len(rows),
                "included": len(included),
                "total": total,
                "count": request.count,
                "offset": request.offset,
                "params": sorted({c.key for c in request.clauses}),
            },
        )
        return rows, total, included

    # ── Delete ────────────────────────────────────────────────────────────
    # create_full()/patch_full() live in full.py.

    async def delete(self, location_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(LocationModel).where(LocationModel.location_id == location_id)
            loc = (await session.execute(stmt)).scalars().first()
            if not loc:
                return False
            try:
                await session.delete(loc)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
