from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.specimen_definition import (
    SpecimenDefinitionModel,
    SpecimenDefinitionTypeCollectedCoding,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for SpecimenDefinition."""

    async def get_by_specimen_definition_id(
        self, specimen_definition_id: int
    ) -> SpecimenDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(SpecimenDefinitionModel).where(
                    SpecimenDefinitionModel.specimen_definition_id == specimen_definition_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_specimen_definition_id_in_org(
        self, specimen_definition_id: int, org_id: str
    ) -> SpecimenDefinitionModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(SpecimenDefinitionModel).where(
                    SpecimenDefinitionModel.specimen_definition_id == specimen_definition_id,
                    SpecimenDefinitionModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def specimen_definition_belongs_to_org(
        self, specimen_definition_id: int, org_id: str
    ) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(SpecimenDefinitionModel.id)).where(
                SpecimenDefinitionModel.specimen_definition_id == specimen_definition_id,
                SpecimenDefinitionModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        identifier: str | None = None,
        type_collected: str | None = None,
    ):
        stmt = stmt.where(SpecimenDefinitionModel.tenant_id == org_id)

        if identifier:
            if "|" in identifier:
                sys, val = identifier.split("|", 1)
                if sys:
                    stmt = stmt.where(SpecimenDefinitionModel.identifier_system == sys)
                if val:
                    stmt = stmt.where(SpecimenDefinitionModel.identifier_value == val)
            else:
                stmt = stmt.where(SpecimenDefinitionModel.identifier_value == identifier)

        if type_collected:
            conditions = [
                SpecimenDefinitionTypeCollectedCoding.specimen_definition_pk == SpecimenDefinitionModel.id
            ]
            if "|" in type_collected:
                sys, val = type_collected.split("|", 1)
                if sys:
                    conditions.append(SpecimenDefinitionTypeCollectedCoding.system == sys)
                if val:
                    conditions.append(SpecimenDefinitionTypeCollectedCoding.code == val)
            else:
                conditions.append(SpecimenDefinitionTypeCollectedCoding.code == type_collected)
            stmt = apply_child_exists_filter(
                stmt,
                select(SpecimenDefinitionTypeCollectedCoding.id).where(*conditions),
            )

        return stmt

    async def list(
        self,
        *,
        org_id: str,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
        identifier: str | None = None,
        type_collected: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[SpecimenDefinitionModel], int]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(SpecimenDefinitionModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                identifier=identifier,
                type_collected=type_collected,
            )

            data_stmt = select(SpecimenDefinitionModel)
            data_stmt = self._apply_list_filters(
                data_stmt,
                org_id=org_id,
                identifier=identifier,
                type_collected=type_collected,
            )
            data_stmt = _with_relationships(data_stmt)

            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                SpecimenDefinitionModel.specimen_definition_id,
                default_desc=True,
            )

            rows, total = await self._execute_paginated(
                session,
                data_stmt,
                count_stmt,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
            return list(rows), total or 0

    async def delete(self, specimen_definition_id: int, org_id: str) -> bool:
        """Deletes a SpecimenDefinition resource if it belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(SpecimenDefinitionModel).where(
                    SpecimenDefinitionModel.specimen_definition_id == specimen_definition_id,
                    SpecimenDefinitionModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False

            await session.delete(model)
            await session.commit()
            return True
