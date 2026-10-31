from sqlalchemy import delete as sql_delete, func, select

from app.core.filters import apply_child_exists_filter, array_contains
from app.core.pagination import resolve_sort
from app.models.observation_definition import (
    ObservationDefinitionCategory,
    ObservationDefinitionCategoryCoding,
    ObservationDefinitionCodeCoding,
    ObservationDefinitionIdentifier,
    ObservationDefinitionMethodCoding,
    ObservationDefinitionModel,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships


class _CoreMixin:
    """Read, list, and delete operations for ObservationDefinition."""

    async def get_by_observation_definition_id(
        self, observation_definition_id: int
    ) -> ObservationDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(ObservationDefinitionModel).where(
                ObservationDefinitionModel.observation_definition_id
                == observation_definition_id
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_observation_definition_id_in_org(
        self, observation_definition_id: int, org_id: str
    ) -> ObservationDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(ObservationDefinitionModel).where(
                ObservationDefinitionModel.observation_definition_id
                == observation_definition_id,
                ObservationDefinitionModel.tenant_id == org_id,
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def observation_definition_belongs_to_org(
        self, observation_definition_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(ObservationDefinitionModel.id).where(
                ObservationDefinitionModel.observation_definition_id
                == observation_definition_id,
                ObservationDefinitionModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        code: str | None = None,
        category: str | None = None,
        method: str | None = None,
        identifier: str | None = None,
        permitted_data_type: str | None = None,
    ):
        stmt = stmt.where(ObservationDefinitionModel.tenant_id == org_id)
        if permitted_data_type:
            val = (
                permitted_data_type.value
                if hasattr(permitted_data_type, "value")
                else permitted_data_type
            )
            stmt = stmt.where(
                array_contains(ObservationDefinitionModel.permitted_data_type, val)
            )
        if code:
            stmt = apply_child_exists_filter(
                stmt,
                select(ObservationDefinitionCodeCoding.id).where(
                    ObservationDefinitionCodeCoding.observation_definition_pk
                    == ObservationDefinitionModel.id,
                    ObservationDefinitionCodeCoding.code == code,
                ),
            )
        if category:
            stmt = apply_child_exists_filter(
                stmt,
                select(ObservationDefinitionCategoryCoding.id)
                .join(
                    ObservationDefinitionCategory,
                    ObservationDefinitionCategoryCoding.category_id
                    == ObservationDefinitionCategory.id,
                )
                .where(
                    ObservationDefinitionCategory.observation_definition_pk
                    == ObservationDefinitionModel.id,
                    ObservationDefinitionCategoryCoding.code == category,
                ),
            )
        if method:
            stmt = apply_child_exists_filter(
                stmt,
                select(ObservationDefinitionMethodCoding.id).where(
                    ObservationDefinitionMethodCoding.observation_definition_pk
                    == ObservationDefinitionModel.id,
                    ObservationDefinitionMethodCoding.code == method,
                ),
            )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(ObservationDefinitionIdentifier.id).where(
                    ObservationDefinitionIdentifier.observation_definition_pk
                    == ObservationDefinitionModel.id,
                    ObservationDefinitionIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str,
        code: str | None = None,
        category: str | None = None,
        method: str | None = None,
        identifier: str | None = None,
        permitted_data_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ObservationDefinitionModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "code": code,
                "category": category,
                "method": method,
                "identifier": identifier,
                "permitted_data_type": permitted_data_type,
            }
            base = self._apply_list_filters(
                _with_relationships(select(ObservationDefinitionModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(ObservationDefinitionModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=ObservationDefinitionModel.observation_definition_id,
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
            return list(rows), total

    async def delete(self, observation_definition_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = sql_delete(ObservationDefinitionModel).where(
                ObservationDefinitionModel.observation_definition_id
                == observation_definition_id
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
