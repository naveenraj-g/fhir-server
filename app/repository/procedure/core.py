from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_date_range_filter,
    apply_token_filter,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.procedure import (
    ProcedureBasedOn,
    ProcedureCategoryCoding,
    ProcedureCodeCoding,
    ProcedureIdentifier,
    ProcedureModel,
    ProcedurePartOf,
    ProcedureStatus,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_based_on_ref,
    _parse_encounter_ref,
    _parse_location_ref,
    _parse_part_of_ref,
    _parse_subject_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for Procedure."""

    async def get_by_procedure_id(self, procedure_id: int) -> ProcedureModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ProcedureModel).where(ProcedureModel.procedure_id == procedure_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_procedure_id_in_org(
        self, procedure_id: int, org_id: str
    ) -> ProcedureModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ProcedureModel).where(
                    ProcedureModel.procedure_id == procedure_id,
                    ProcedureModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def procedure_belongs_to_org(self, procedure_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(ProcedureModel.id).where(
                ProcedureModel.procedure_id == procedure_id,
                ProcedureModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | ProcedureStatus | None = None,
        patient: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        code: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        location: str | None = None,
        based_on: str | None = None,
        part_of: str | None = None,
        category: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(ProcedureModel.tenant_id == org_id)
        if status:
            stmt = apply_token_filter(stmt, ProcedureModel.status, status)

        subj_filter = patient or subject
        if subj_filter:
            s_type, s_id = _parse_subject_ref(subj_filter)
            if s_id:
                stmt = stmt.where(ProcedureModel.subject_id == s_id)
                if s_type:
                    stmt = stmt.where(ProcedureModel.subject_type == s_type)
            else:
                stmt = stmt.where(ProcedureModel.subject_reference == subj_filter)

        if encounter:
            e_type, e_id = _parse_encounter_ref(encounter)
            if e_id:
                stmt = stmt.where(ProcedureModel.encounter_id == e_id)
                if e_type:
                    stmt = stmt.where(ProcedureModel.encounter_type == e_type)
            else:
                stmt = stmt.where(ProcedureModel.encounter_reference == encounter)

        if location:
            l_type, l_id = _parse_location_ref(location)
            if l_id:
                stmt = stmt.where(ProcedureModel.location_id == l_id)
                if l_type:
                    stmt = stmt.where(ProcedureModel.location_type == l_type)
            else:
                stmt = stmt.where(ProcedureModel.location_reference == location)

        if code:
            stmt = stmt.where(
                or_(
                    ProcedureModel.code_text.ilike(f"%{code}%"),
                    ProcedureModel.id.in_(
                        select(ProcedureCodeCoding.procedure_pk).where(
                            ProcedureCodeCoding.code == code
                        )
                    ),
                )
            )

        if category:
            stmt = stmt.where(
                or_(
                    ProcedureModel.category_text.ilike(f"%{category}%"),
                    ProcedureModel.id.in_(
                        select(ProcedureCategoryCoding.procedure_pk).where(
                            ProcedureCategoryCoding.code == category
                        )
                    ),
                )
            )

        if date_val:
            stmt = stmt.where(
                func.date(ProcedureModel.performed_date_time) == date_val
            )
        elif date_from or date_to:
            stmt = apply_date_range_filter(
                stmt,
                ProcedureModel.performed_date_time,
                date_from=date_from,
                date_to=date_to,
            )

        if based_on:
            bo_type, bo_id = _parse_based_on_ref(based_on)
            if bo_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(ProcedureBasedOn.id).where(
                        ProcedureBasedOn.procedure_pk == ProcedureModel.id,
                        ProcedureBasedOn.reference_id == bo_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(ProcedureBasedOn.id).where(
                        ProcedureBasedOn.procedure_pk == ProcedureModel.id,
                        ProcedureBasedOn.reference_reference == based_on,
                    ),
                )

        if part_of:
            po_type, po_id = _parse_part_of_ref(part_of)
            if po_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(ProcedurePartOf.id).where(
                        ProcedurePartOf.procedure_pk == ProcedureModel.id,
                        ProcedurePartOf.reference_id == po_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(ProcedurePartOf.id).where(
                        ProcedurePartOf.procedure_pk == ProcedureModel.id,
                        ProcedurePartOf.reference_reference == part_of,
                    ),
                )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(ProcedureIdentifier.id).where(
                    ProcedureIdentifier.procedure_pk == ProcedureModel.id,
                    ProcedureIdentifier.value == identifier,
                ),
            )

        return stmt

    async def list(
        self,
        org_id: str,
        status: str | None = None,
        patient: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        code: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        location: str | None = None,
        based_on: str | None = None,
        part_of: str | None = None,
        category: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ProcedureModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = dict(
                org_id=org_id,
                status=status,
                patient=patient,
                subject=subject,
                encounter=encounter,
                code=code,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
                location=location,
                based_on=based_on,
                part_of=part_of,
                category=category,
                identifier=identifier,
            )
            base = self._apply_list_filters(select(ProcedureModel), **filter_kwargs)
            base = _with_relationships(base)
            count_stmt = self._apply_list_filters(
                select(func.count()).select_from(ProcedureModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                ProcedureModel.procedure_id,
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

    async def delete(self, procedure_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(ProcedureModel).where(ProcedureModel.procedure_id == procedure_id)
            procedure = (await session.execute(stmt)).scalars().first()
            if not procedure:
                return False
            await session.delete(procedure)
            await session.commit()
            return True
