from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.medication_request import (
    MedicationRequestIdentifier,
    MedicationRequestIntent,
    MedicationRequestModel,
    MedicationRequestStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the MedicationRequest parent row (no sub-resources).
    Default (gateway-trusted) pattern — same as QuestionnaireResponse/
    ServiceRequest: no org-scoped existence check or ownership
    enforcement here at all."""

    async def get_by_medication_request_id(self, medication_request_id: int) -> MedicationRequestModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationRequestModel).where(MedicationRequestModel.medication_request_id == medication_request_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_medication_request_id_in_org(
        self, medication_request_id: int, org_id: str
    ) -> MedicationRequestModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationRequestModel).where(
                    MedicationRequestModel.medication_request_id == medication_request_id,
                    MedicationRequestModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def medication_request_belongs_to_org(self, medication_request_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationRequestModel.id).where(
                MedicationRequestModel.medication_request_id == medication_request_id,
                MedicationRequestModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: MedicationRequestStatus | None = None,
        intent: MedicationRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(MedicationRequestModel.tenant_id == org_id)
        stmt = apply_token_filter(stmt, MedicationRequestModel.status, status)
        stmt = apply_token_filter(stmt, MedicationRequestModel.intent, intent)
        if subject:
            stmt = stmt.where(MedicationRequestModel.subject_reference == subject)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(MedicationRequestIdentifier.id).where(
                    MedicationRequestIdentifier.medication_request_pk == MedicationRequestModel.id,
                    MedicationRequestIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: MedicationRequestStatus | None = None,
        intent: MedicationRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[MedicationRequestModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "intent": intent,
                "subject": subject,
                "identifier": identifier,
            }
            base = self._apply_list_filters(_with_relationships(select(MedicationRequestModel)), **filter_kwargs)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(MedicationRequestModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort, _SORTABLE_FIELDS, default_column=MedicationRequestModel.medication_request_id, default_desc=True
            )
            rows, total = await self._execute_paginated(
                session, base, count_base, sort_column=sort_column, sort_desc=sort_desc,
                limit=limit, offset=offset, total_mode=total_mode,
            )
        logger.debug(
            "MedicationRequests listed",
            extra={
                "event": "medication_request.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    async def delete(self, medication_request_id: int) -> bool:
        """Every sub-resource here is a plain two/three-level
        child/grandchild (no self-referential or mutual-recursion gotcha
        like QuestionnaireResponse's item/answer), so a plain ORM
        `session.delete()` with every relationship's own
        `cascade="all, delete-orphan"` is safe and sufficient."""
        async with self.session_factory() as session:
            stmt = select(MedicationRequestModel).where(MedicationRequestModel.medication_request_id == medication_request_id)
            mr = (await session.execute(stmt)).scalars().first()
            if not mr:
                return False
            try:
                await session.delete(mr)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
