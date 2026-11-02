from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    ArrayContains,
    apply_child_exists_filter,
    apply_date_range_filter,
    apply_token_filter,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.family_member_history import (
    FamilyMemberHistoryCondition,
    FamilyMemberHistoryConditionCodeCoding,
    FamilyMemberHistoryIdentifier,
    FamilyMemberHistoryModel,
    FamilyMemberHistoryRelationshipCoding,
    FamilyMemberHistorySexCoding,
    FamilyMemberHistoryStatus,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_patient_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for FamilyMemberHistory."""

    async def get_by_family_member_history_id(
        self, family_member_history_id: int
    ) -> FamilyMemberHistoryModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(FamilyMemberHistoryModel).where(
                    FamilyMemberHistoryModel.family_member_history_id
                    == family_member_history_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_family_member_history_id_in_org(
        self, family_member_history_id: int, org_id: str
    ) -> FamilyMemberHistoryModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(FamilyMemberHistoryModel).where(
                    FamilyMemberHistoryModel.family_member_history_id
                    == family_member_history_id,
                    FamilyMemberHistoryModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def family_member_history_belongs_to_org(
        self, family_member_history_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(FamilyMemberHistoryModel.id).where(
                FamilyMemberHistoryModel.family_member_history_id
                == family_member_history_id,
                FamilyMemberHistoryModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | FamilyMemberHistoryStatus | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        relationship: str | None = None,
        sex: str | None = None,
        code: str | None = None,
        identifier: str | None = None,
        instantiates: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(FamilyMemberHistoryModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, FamilyMemberHistoryModel.status, status)

        if patient:
            p_type, p_id = _parse_patient_ref(patient)
            if p_id:
                stmt = stmt.where(FamilyMemberHistoryModel.patient_id == p_id)
            else:
                stmt = stmt.where(FamilyMemberHistoryModel.patient_reference == patient)

        if date_val or date_from or date_to:
            stmt = apply_date_range_filter(
                stmt,
                FamilyMemberHistoryModel.date,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
            )

        if relationship:
            stmt = stmt.where(
                or_(
                    FamilyMemberHistoryModel.relationship_text.ilike(f"%{relationship}%"),
                    FamilyMemberHistoryModel.id.in_(
                        select(FamilyMemberHistoryRelationshipCoding.family_member_history_pk).where(
                            or_(
                                FamilyMemberHistoryRelationshipCoding.code == relationship,
                                FamilyMemberHistoryRelationshipCoding.display.ilike(f"%{relationship}%"),
                            )
                        )
                    ),
                )
            )

        if sex:
            stmt = stmt.where(
                or_(
                    FamilyMemberHistoryModel.sex_text.ilike(f"%{sex}%"),
                    FamilyMemberHistoryModel.id.in_(
                        select(FamilyMemberHistorySexCoding.family_member_history_pk).where(
                            or_(
                                FamilyMemberHistorySexCoding.code == sex,
                                FamilyMemberHistorySexCoding.display.ilike(f"%{sex}%"),
                            )
                        )
                    ),
                )
            )

        if code:
            cond_subquery = select(FamilyMemberHistoryCondition.family_member_history_pk).where(
                or_(
                    FamilyMemberHistoryCondition.code_text.ilike(f"%{code}%"),
                    FamilyMemberHistoryCondition.id.in_(
                        select(FamilyMemberHistoryConditionCodeCoding.family_member_history_condition_id).where(
                            or_(
                                FamilyMemberHistoryConditionCodeCoding.code == code,
                                FamilyMemberHistoryConditionCodeCoding.display.ilike(f"%{code}%"),
                            )
                        )
                    ),
                )
            )
            stmt = stmt.where(FamilyMemberHistoryModel.id.in_(cond_subquery))

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                FamilyMemberHistoryModel.id,
                FamilyMemberHistoryIdentifier.family_member_history_pk,
                identifier,
                FamilyMemberHistoryIdentifier.system,
                FamilyMemberHistoryIdentifier.value,
            )

        if instantiates:
            inst_val = (
                instantiates.value
                if hasattr(instantiates, "value")
                else str(instantiates)
            )
            stmt = stmt.where(
                or_(
                    ArrayContains(FamilyMemberHistoryModel.instantiates_canonical, inst_val),
                    ArrayContains(FamilyMemberHistoryModel.instantiates_uri, inst_val),
                )
            )

        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: str | FamilyMemberHistoryStatus | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        relationship: str | None = None,
        sex: str | None = None,
        code: str | None = None,
        identifier: str | None = None,
        instantiates: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[FamilyMemberHistoryModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = dict(
                org_id=org_id,
                status=status,
                patient=patient,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
                relationship=relationship,
                sex=sex,
                code=code,
                identifier=identifier,
                instantiates=instantiates,
            )
            base = self._apply_list_filters(
                select(FamilyMemberHistoryModel), **filter_kwargs
            )
            base = _with_relationships(base)
            count_stmt = self._apply_list_filters(
                select(func.count()).select_from(FamilyMemberHistoryModel),
                **filter_kwargs,
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                FamilyMemberHistoryModel.family_member_history_id,
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

    async def delete(self, family_member_history_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(FamilyMemberHistoryModel).where(
                FamilyMemberHistoryModel.family_member_history_id
                == family_member_history_id,
                FamilyMemberHistoryModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True
