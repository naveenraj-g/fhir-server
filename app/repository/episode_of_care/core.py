from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.episode_of_care import EpisodeOfCareModel

from .search import episode_of_care_search

logger = get_logger(__name__)

_M = EpisodeOfCareModel


class _CoreMixin:
    """Reads, search and delete. Every read loads only the episode_of_care
    row itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_episode_of_care_id(self, episode_of_care_id: int) -> _M | None:
        async with self.session_factory() as session:
            stmt = select(_M).where(_M.episode_of_care_id == episode_of_care_id)
            return (await session.execute(stmt)).scalars().first()

    async def get_by_episode_of_care_id_in_org(
        self, episode_of_care_id: int, org_id: str
    ) -> _M | None:
        """Lookup scoped to org_id — returns None unless the episode_of_care
        exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(_M).where(
                _M.episode_of_care_id == episode_of_care_id, _M.tenant_id == org_id
            )
            return (await session.execute(stmt)).scalars().first()

    async def episode_of_care_belongs_to_org(
        self, episode_of_care_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the episode_of_care exists AND
        belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(_M.id).where(
                _M.episode_of_care_id == episode_of_care_id, _M.tenant_id == org_id
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
                registry=episode_of_care_search(),
                request=request,
                ctx=ctx,
                tiebreak=_M.episode_of_care_id,
            )
        logger.debug(
            "EpisodeOfCares searched",
            extra={
                "event": "episode_of_care.searched",
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

    async def delete(self, episode_of_care_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(_M).where(_M.episode_of_care_id == episode_of_care_id)
            episode_of_care = (await session.execute(stmt)).scalars().first()
            if not episode_of_care:
                return False
            try:
                await session.delete(episode_of_care)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
