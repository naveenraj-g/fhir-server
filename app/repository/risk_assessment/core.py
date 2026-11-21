from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.risk_assessment import RiskAssessmentModel

from .search import risk_assessment_search

logger = get_logger(__name__)

_M = RiskAssessmentModel


class _CoreMixin:
    """Reads, search and delete. Every read loads only the risk_assessment
    row itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_risk_assessment_id(self, risk_assessment_id: int) -> _M | None:
        async with self.session_factory() as session:
            stmt = select(_M).where(_M.risk_assessment_id == risk_assessment_id)
            return (await session.execute(stmt)).scalars().first()

    async def get_by_risk_assessment_id_in_org(self, risk_assessment_id: int, org_id: str) -> _M | None:
        """Lookup scoped to org_id — returns None unless the risk_assessment
        exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(_M).where(_M.risk_assessment_id == risk_assessment_id, _M.tenant_id == org_id)
            return (await session.execute(stmt)).scalars().first()

    async def risk_assessment_belongs_to_org(self, risk_assessment_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the risk_assessment exists AND
        belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(_M.id).where(_M.risk_assessment_id == risk_assessment_id, _M.tenant_id == org_id)
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
                registry=risk_assessment_search(),
                request=request,
                ctx=ctx,
                tiebreak=_M.risk_assessment_id,
            )
        logger.debug(
            "RiskAssessments searched",
            extra={
                "event": "risk_assessment.searched",
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

    async def delete(self, risk_assessment_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(_M).where(_M.risk_assessment_id == risk_assessment_id)
            risk_assessment = (await session.execute(stmt)).scalars().first()
            if not risk_assessment:
                return False
            try:
                await session.delete(risk_assessment)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
