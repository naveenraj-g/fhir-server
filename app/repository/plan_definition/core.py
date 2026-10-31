from sqlalchemy import delete as sql_delete, func, select

from app.core.filters import apply_child_exists_filter
from app.core.pagination import resolve_sort
from app.models.plan_definition import (
    PlanDefinitionIdentifier,
    PlanDefinitionModel,
    PlanDefinitionStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships


class _CoreMixin:
    """Read, list, and delete operations for PlanDefinition."""

    async def get_by_plan_definition_id(
        self, plan_definition_id: int
    ) -> PlanDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(PlanDefinitionModel).where(
                PlanDefinitionModel.plan_definition_id == plan_definition_id
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_plan_definition_id_in_org(
        self, plan_definition_id: int, org_id: str
    ) -> PlanDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(PlanDefinitionModel).where(
                PlanDefinitionModel.plan_definition_id == plan_definition_id,
                PlanDefinitionModel.tenant_id == org_id,
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def plan_definition_belongs_to_org(
        self, plan_definition_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(PlanDefinitionModel.id).where(
                PlanDefinitionModel.plan_definition_id == plan_definition_id,
                PlanDefinitionModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        url: str | None = None,
        version: str | None = None,
        identifier: str | None = None,
    ):
        stmt = stmt.where(PlanDefinitionModel.tenant_id == org_id)
        if name:
            stmt = stmt.where(PlanDefinitionModel.name.ilike(f"%{name}%"))
        if title:
            stmt = stmt.where(PlanDefinitionModel.title.ilike(f"%{title}%"))
        if status:
            val = status.value if hasattr(status, "value") else status
            stmt = stmt.where(PlanDefinitionModel.status == PlanDefinitionStatus(val))
        if url:
            stmt = stmt.where(PlanDefinitionModel.url == url)
        if version:
            stmt = stmt.where(PlanDefinitionModel.version == version)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(PlanDefinitionIdentifier.id).where(
                    PlanDefinitionIdentifier.plan_definition_pk
                    == PlanDefinitionModel.id,
                    PlanDefinitionIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        url: str | None = None,
        version: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PlanDefinitionModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "name": name,
                "title": title,
                "status": status,
                "url": url,
                "version": version,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(PlanDefinitionModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PlanDefinitionModel),
                **filter_kwargs,
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=PlanDefinitionModel.plan_definition_id,
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

    async def delete(self, plan_definition_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = sql_delete(PlanDefinitionModel).where(
                PlanDefinitionModel.plan_definition_id == plan_definition_id
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
