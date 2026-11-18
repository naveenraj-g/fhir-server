from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.practitioner import PractitionerModel

from .search import practitioner_search

logger = get_logger(__name__)


class _CoreMixin:
    """Reads, search and delete. Every read loads only the practitioner row
    itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_practitioner_id(
        self, practitioner_id: int
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_practitioner_id_in_org(
        self, practitioner_id: int, org_id: str
    ) -> PractitionerModel | None:
        """Lookup scoped to org_id — returns None unless the practitioner
        exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id,
                PractitionerModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalars().first()

    async def practitioner_belongs_to_org(
        self, practitioner_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the practitioner exists AND belongs
        to org_id."""
        async with self.session_factory() as session:
            stmt = select(PractitionerModel.id).where(
                PractitionerModel.practitioner_id == practitioner_id,
                PractitionerModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    # ── End-user link ─────────────────────────────────────────────────────
    # `user_id` ties a practitioner record to the IAM user who acts as that
    # practitioner (what `/me` scopes to). It is not part of the FHIR
    # resource, so it is read and written here, not through create/patch.

    async def get_by_user_id_in_org(
        self, user_id: str, org_id: str
    ) -> PractitionerModel | None:
        """The practitioner in org_id linked to user_id, if any."""
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.user_id == user_id,
                PractitionerModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalars().first()

    async def set_user_id(
        self, practitioner_id: int, user_id: str | None, updated_by: str | None
    ) -> PractitionerModel | None:
        """Link (or, with None, unlink) the end-user. Does not touch
        `content` or the search index."""
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id
            )
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            practitioner.user_id = user_id
            if updated_by is not None:
                practitioner.updated_by = updated_by
            try:
                await session.commit()
                await session.refresh(practitioner)
            except Exception:
                await session.rollback()
                raise
            return practitioner

    # ── Search ────────────────────────────────────────────────────────────
    # FHIR R4 search — every parameter, modifier and result parameter is
    # declared in search.py's registry and run by app.fhir.search.

    async def search(
        self, request: SearchRequest, ctx: SearchContext, user_id: str | None = None
    ):
        """(matches for this page, total or None, included (type, row)
        pairs). Always scoped to ctx.tenant_id; `user_id` additionally
        restricts to one end-user's own records (the `/me` route)."""
        extra = [PractitionerModel.user_id == user_id] if user_id is not None else []
        async with self.session_factory() as session:
            rows, total, included = await execute_search(
                session,
                model=PractitionerModel,
                registry=practitioner_search(),
                request=request,
                ctx=ctx,
                tiebreak=PractitionerModel.practitioner_id,
                extra_conditions=extra,
            )
        logger.debug(
            "Practitioners searched",
            extra={
                "event": "practitioner.searched",
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

    async def delete(self, practitioner_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id
            )
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return False
            try:
                await session.delete(practitioner)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
