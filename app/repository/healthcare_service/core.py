from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.healthcare_service import HealthcareServiceModel

from .search import healthcare_service_search

logger = get_logger(__name__)


class _CoreMixin:
    """Reads, search and delete. Every read loads only the healthcare_service row
    itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_healthcare_service_id(
        self, healthcare_service_id: int
    ) -> HealthcareServiceModel | None:
        async with self.session_factory() as session:
            stmt = select(HealthcareServiceModel).where(
                HealthcareServiceModel.healthcare_service_id == healthcare_service_id
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_healthcare_service_id_in_org(
        self, healthcare_service_id: int, org_id: str
    ) -> HealthcareServiceModel | None:
        """Lookup scoped to org_id — returns None unless the healthcare_service
        exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(HealthcareServiceModel).where(
                HealthcareServiceModel.healthcare_service_id == healthcare_service_id,
                HealthcareServiceModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalars().first()

    async def healthcare_service_belongs_to_org(
        self, healthcare_service_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the healthcare_service exists AND belongs
        to org_id."""
        async with self.session_factory() as session:
            stmt = select(HealthcareServiceModel.id).where(
                HealthcareServiceModel.healthcare_service_id == healthcare_service_id,
                HealthcareServiceModel.tenant_id == org_id,
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
                model=HealthcareServiceModel,
                registry=healthcare_service_search(),
                request=request,
                ctx=ctx,
                tiebreak=HealthcareServiceModel.healthcare_service_id,
            )
        logger.debug(
            "HealthcareServices searched",
            extra={
                "event": "healthcare_service.searched",
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

    async def delete(self, healthcare_service_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(HealthcareServiceModel).where(
                HealthcareServiceModel.healthcare_service_id == healthcare_service_id
            )
            healthcare_service = (await session.execute(stmt)).scalars().first()
            if not healthcare_service:
                return False
            try:
                await session.delete(healthcare_service)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
