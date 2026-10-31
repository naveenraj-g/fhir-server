from sqlalchemy import delete as sql_delete, func, select

from app.core.filters import apply_child_exists_filter
from app.core.pagination import resolve_sort
from app.models.activity_definition import (
    ActivityDefinitionIdentifier,
    ActivityDefinitionIntent,
    ActivityDefinitionKind,
    ActivityDefinitionModel,
    ActivityDefinitionPriority,
    ActivityDefinitionStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships


class _CoreMixin:
    """Read, list, and delete operations for ActivityDefinition."""

    async def get_by_activity_definition_id(
        self, activity_definition_id: int
    ) -> ActivityDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(ActivityDefinitionModel).where(
                ActivityDefinitionModel.activity_definition_id
                == activity_definition_id
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_activity_definition_id_in_org(
        self, activity_definition_id: int, org_id: str
    ) -> ActivityDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(ActivityDefinitionModel).where(
                ActivityDefinitionModel.activity_definition_id
                == activity_definition_id,
                ActivityDefinitionModel.tenant_id == org_id,
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def activity_definition_belongs_to_org(
        self, activity_definition_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(ActivityDefinitionModel.id).where(
                ActivityDefinitionModel.activity_definition_id
                == activity_definition_id,
                ActivityDefinitionModel.tenant_id == org_id,
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
        kind: str | None = None,
        intent: str | None = None,
        priority: str | None = None,
        identifier: str | None = None,
    ):
        stmt = stmt.where(ActivityDefinitionModel.tenant_id == org_id)
        if name:
            stmt = stmt.where(ActivityDefinitionModel.name.ilike(f"%{name}%"))
        if title:
            stmt = stmt.where(ActivityDefinitionModel.title.ilike(f"%{title}%"))
        if status:
            val = status.value if hasattr(status, "value") else status
            stmt = stmt.where(ActivityDefinitionModel.status == ActivityDefinitionStatus(val))
        if kind:
            val = kind.value if hasattr(kind, "value") else kind
            stmt = stmt.where(ActivityDefinitionModel.kind == ActivityDefinitionKind(val))
        if intent:
            val = intent.value if hasattr(intent, "value") else intent
            stmt = stmt.where(ActivityDefinitionModel.intent == ActivityDefinitionIntent(val))
        if priority:
            val = priority.value if hasattr(priority, "value") else priority
            stmt = stmt.where(ActivityDefinitionModel.priority == ActivityDefinitionPriority(val))
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(ActivityDefinitionIdentifier.id).where(
                    ActivityDefinitionIdentifier.activity_definition_pk
                    == ActivityDefinitionModel.id,
                    ActivityDefinitionIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        kind: str | None = None,
        intent: str | None = None,
        priority: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ActivityDefinitionModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "name": name,
                "title": title,
                "status": status,
                "kind": kind,
                "intent": intent,
                "priority": priority,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(ActivityDefinitionModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(ActivityDefinitionModel),
                **filter_kwargs,
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=ActivityDefinitionModel.activity_definition_id,
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

    async def delete(self, activity_definition_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = sql_delete(ActivityDefinitionModel).where(
                ActivityDefinitionModel.activity_definition_id
                == activity_definition_id
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
