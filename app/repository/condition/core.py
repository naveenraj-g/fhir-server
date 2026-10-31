from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.condition import (
    ConditionCategory,
    ConditionCategoryCoding,
    ConditionClinicalStatusCoding,
    ConditionCodeCoding,
    ConditionIdentifier,
    ConditionModel,
    ConditionSeverityCoding,
    ConditionVerificationStatusCoding,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for Condition."""

    async def get_by_condition_id(self, condition_id: int) -> ConditionModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ConditionModel).where(ConditionModel.condition_id == condition_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_condition_id_in_org(
        self, condition_id: int, org_id: str
    ) -> ConditionModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ConditionModel).where(
                    ConditionModel.condition_id == condition_id,
                    ConditionModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def condition_belongs_to_org(self, condition_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(ConditionModel.id).where(
                ConditionModel.condition_id == condition_id,
                ConditionModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        clinical_status: str | None = None,
        verification_status: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        code: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(ConditionModel.tenant_id == org_id)
        if clinical_status:
            stmt = apply_child_exists_filter(
                stmt,
                select(ConditionClinicalStatusCoding.id).where(
                    ConditionClinicalStatusCoding.condition_pk == ConditionModel.id,
                    ConditionClinicalStatusCoding.code == clinical_status,
                ),
            )
        if verification_status:
            stmt = apply_child_exists_filter(
                stmt,
                select(ConditionVerificationStatusCoding.id).where(
                    ConditionVerificationStatusCoding.condition_pk == ConditionModel.id,
                    ConditionVerificationStatusCoding.code == verification_status,
                ),
            )
        if category:
            stmt = apply_child_exists_filter(
                stmt,
                select(ConditionCategoryCoding.id).join(
                    ConditionCategory, ConditionCategoryCoding.condition_category_id == ConditionCategory.id
                ).where(
                    ConditionCategory.condition_pk == ConditionModel.id,
                    ConditionCategoryCoding.code == category,
                ),
            )
        if severity:
            stmt = apply_child_exists_filter(
                stmt,
                select(ConditionSeverityCoding.id).where(
                    ConditionSeverityCoding.condition_pk == ConditionModel.id,
                    ConditionSeverityCoding.code == severity,
                ),
            )
        if code:
            stmt = apply_child_exists_filter(
                stmt,
                select(ConditionCodeCoding.id).where(
                    ConditionCodeCoding.condition_pk == ConditionModel.id,
                    ConditionCodeCoding.code == code,
                ),
            )
        if subject:
            stmt = stmt.where(ConditionModel.subject_reference == subject)
        if encounter:
            stmt = stmt.where(ConditionModel.encounter_reference == encounter)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(ConditionIdentifier.id).where(
                    ConditionIdentifier.condition_pk == ConditionModel.id,
                    ConditionIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        clinical_status: str | None = None,
        verification_status: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        code: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ConditionModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "clinical_status": clinical_status,
                "verification_status": verification_status,
                "category": category,
                "severity": severity,
                "code": code,
                "subject": subject,
                "encounter": encounter,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(ConditionModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(ConditionModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=ConditionModel.condition_id,
                default_desc=True,
            )
            rows, total = await self._execute_paginated(
                session,
                base,
                count_base,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
        logger.debug(
            "Conditions listed",
            extra={
                "event": "condition.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    async def delete(self, condition_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(ConditionModel).where(ConditionModel.condition_id == condition_id)
            cond = (await session.execute(stmt)).scalars().first()
            if not cond:
                return False
            try:
                await session.delete(cond)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
