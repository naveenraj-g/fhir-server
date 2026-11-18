from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.search import SearchContext, SearchRequest
from app.fhir.search.execute import execute_search
from app.models.patient import PatientModel

from .search import patient_search

logger = get_logger(__name__)


class _CoreMixin:
    """Reads, search and delete. Every read loads only the patient row
    itself — the response is served from `content`, so the search-index
    child tables are never eager-loaded here."""

    async def get_by_patient_id(
        self, patient_id: int
    ) -> PatientModel | None:
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(
                PatientModel.patient_id == patient_id
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_patient_id_in_org(
        self, patient_id: int, org_id: str
    ) -> PatientModel | None:
        """Lookup scoped to org_id — returns None unless the patient
        exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(
                PatientModel.patient_id == patient_id,
                PatientModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalars().first()

    async def patient_belongs_to_org(
        self, patient_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the patient exists AND belongs
        to org_id."""
        async with self.session_factory() as session:
            stmt = select(PatientModel.id).where(
                PatientModel.patient_id == patient_id,
                PatientModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    # ── End-user link ─────────────────────────────────────────────────────
    # `user_id` ties a patient record to the IAM user who acts as that
    # patient (what `/me` scopes to). It is not part of the FHIR
    # resource, so it is read and written here, not through create/patch.

    async def get_by_user_id_in_org(
        self, user_id: str, org_id: str
    ) -> PatientModel | None:
        """The patient in org_id linked to user_id, if any."""
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(
                PatientModel.user_id == user_id,
                PatientModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalars().first()

    async def set_user_id(
        self, patient_id: int, user_id: str | None, updated_by: str | None
    ) -> PatientModel | None:
        """Link (or, with None, unlink) the end-user. Does not touch
        `content` or the search index."""
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(
                PatientModel.patient_id == patient_id
            )
            patient = (await session.execute(stmt)).scalars().first()
            if not patient:
                return None
            patient.user_id = user_id
            if updated_by is not None:
                patient.updated_by = updated_by
            try:
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise
            return patient

    # ── Search ────────────────────────────────────────────────────────────
    # FHIR R4 search — every parameter, modifier and result parameter is
    # declared in search.py's registry and run by app.fhir.search.

    async def search(
        self, request: SearchRequest, ctx: SearchContext, user_id: str | None = None
    ):
        """(matches for this page, total or None, included (type, row)
        pairs). Always scoped to ctx.tenant_id; `user_id` additionally
        restricts to one end-user's own records (the `/me` route)."""
        extra = [PatientModel.user_id == user_id] if user_id is not None else []
        async with self.session_factory() as session:
            rows, total, included = await execute_search(
                session,
                model=PatientModel,
                registry=patient_search(),
                request=request,
                ctx=ctx,
                tiebreak=PatientModel.patient_id,
                extra_conditions=extra,
            )
        logger.debug(
            "Patients searched",
            extra={
                "event": "patient.searched",
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

    async def delete(self, patient_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(
                PatientModel.patient_id == patient_id
            )
            patient = (await session.execute(stmt)).scalars().first()
            if not patient:
                return False
            try:
                await session.delete(patient)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
