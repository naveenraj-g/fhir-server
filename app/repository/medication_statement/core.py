from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_date_range_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.medication_statement import (
    MedicationStatementCategoryCoding,
    MedicationStatementIdentifier,
    MedicationStatementMedicationCoding,
    MedicationStatementModel,
    MedicationStatementStatus,
    MedicationStatementSubjectReferenceType,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for MedicationStatement."""

    async def get_by_medication_statement_id(
        self, medication_statement_id: int
    ) -> MedicationStatementModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationStatementModel).where(
                    MedicationStatementModel.medication_statement_id
                    == medication_statement_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_medication_statement_id_in_org(
        self, medication_statement_id: int, org_id: str
    ) -> MedicationStatementModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationStatementModel).where(
                    MedicationStatementModel.medication_statement_id
                    == medication_statement_id,
                    MedicationStatementModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def medication_statement_belongs_to_org(
        self, medication_statement_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationStatementModel.id).where(
                MedicationStatementModel.medication_statement_id
                == medication_statement_id,
                MedicationStatementModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | MedicationStatementStatus | None = None,
        subject: str | None = None,
        patient: str | None = None,
        code: str | None = None,
        category: str | None = None,
        effective_val: date | datetime | None = None,
        effective_from: date | datetime | None = None,
        effective_to: date | datetime | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(MedicationStatementModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, MedicationStatementModel.status, status)

        subj_filter = subject or patient
        if subj_filter:
            ref_type, ref_id = parse_reference(subj_filter, MedicationStatementSubjectReferenceType)
            if ref_id:
                stmt = stmt.where(MedicationStatementModel.subject_id == ref_id)
            else:
                stmt = stmt.where(MedicationStatementModel.subject_reference == subj_filter)

        if effective_val or effective_from or effective_to:
            stmt = apply_date_range_filter(
                stmt,
                MedicationStatementModel.effective_date_time,
                date_val=effective_val,
                date_from=effective_from,
                date_to=effective_to,
            )

        if code:
            stmt = stmt.where(
                or_(
                    MedicationStatementModel.medication_codeable_concept_text.ilike(f"%{code}%"),
                    MedicationStatementModel.medication_reference.ilike(f"%{code}%"),
                    MedicationStatementModel.id.in_(
                        select(MedicationStatementMedicationCoding.medication_statement_pk).where(
                            or_(
                                MedicationStatementMedicationCoding.code == code,
                                MedicationStatementMedicationCoding.display.ilike(f"%{code}%"),
                            )
                        )
                    ),
                )
            )

        if category:
            stmt = stmt.where(
                or_(
                    MedicationStatementModel.category_text.ilike(f"%{category}%"),
                    MedicationStatementModel.id.in_(
                        select(MedicationStatementCategoryCoding.medication_statement_pk).where(
                            or_(
                                MedicationStatementCategoryCoding.code == category,
                                MedicationStatementCategoryCoding.display.ilike(f"%{category}%"),
                            )
                        )
                    ),
                )
            )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                MedicationStatementModel.id,
                MedicationStatementIdentifier.medication_statement_pk,
                apply_token_filter(
                    select(MedicationStatementIdentifier.id),
                    MedicationStatementIdentifier.value,
                    identifier,
                ),
            )

        return stmt

    async def list(
        self,
        org_id: str,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
        **filter_kwargs,
    ) -> tuple[list[MedicationStatementModel], int | None]:
        async with self.session_factory() as session:
            base = _with_relationships(
                self._apply_list_filters(
                    select(MedicationStatementModel),
                    org_id=org_id,
                    **filter_kwargs,
                )
            )
            count_stmt = self._apply_list_filters(
                select(func.count(MedicationStatementModel.id)),
                org_id=org_id,
                **filter_kwargs,
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                MedicationStatementModel.medication_statement_id,
            )

            rows, total = await self._execute_paginated(
                session,
                base,
                count_stmt,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
            return list(rows), total

    async def delete(self, medication_statement_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationStatementModel).where(
                MedicationStatementModel.medication_statement_id
                == medication_statement_id,
                MedicationStatementModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True
