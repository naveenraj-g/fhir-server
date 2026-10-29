from sqlalchemy import delete as sa_delete, func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_string_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.questionnaire import (
    QuestionnaireIdentifier,
    QuestionnaireItem,
    QuestionnaireItemAnswerOption,
    QuestionnaireItemCoding,
    QuestionnaireItemEnableWhen,
    QuestionnaireItemInitial,
    QuestionnaireModel,
    QuestionnaireStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the Questionnaire parent row (no sub-resources)."""

    async def get_by_questionnaire_id(self, questionnaire_id: int) -> QuestionnaireModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireModel).where(QuestionnaireModel.questionnaire_id == questionnaire_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_questionnaire_id_in_org(
        self, questionnaire_id: int, org_id: str
    ) -> QuestionnaireModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the questionnaire exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireModel).where(
                    QuestionnaireModel.questionnaire_id == questionnaire_id,
                    QuestionnaireModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def questionnaire_belongs_to_org(self, questionnaire_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(QuestionnaireModel.id).where(
                QuestionnaireModel.questionnaire_id == questionnaire_id,
                QuestionnaireModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id=None,
        user_id: str | None = None,
        status: QuestionnaireStatus | None = None,
        url: str | None = None,
        name: str | None = None,
        title: str | None = None,
        publisher: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(QuestionnaireModel.tenant_id == org_id)
        if user_id:
            stmt = stmt.where(QuestionnaireModel.user_id == user_id)
        stmt = apply_token_filter(stmt, QuestionnaireModel.status, status)
        stmt = apply_string_filter(stmt, QuestionnaireModel.url, url, exact=True)
        stmt = apply_string_filter(stmt, QuestionnaireModel.name, name)
        stmt = apply_string_filter(stmt, QuestionnaireModel.title, title)
        stmt = apply_string_filter(stmt, QuestionnaireModel.publisher, publisher)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(QuestionnaireIdentifier.id).where(
                    QuestionnaireIdentifier.questionnaire_pk == QuestionnaireModel.id,
                    QuestionnaireIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        status: QuestionnaireStatus | None = None,
        url: str | None = None,
        name: str | None = None,
        title: str | None = None,
        publisher: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[QuestionnaireModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "user_id": user_id,
                "status": status,
                "url": url,
                "name": name,
                "title": title,
                "publisher": publisher,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(QuestionnaireModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(QuestionnaireModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort, _SORTABLE_FIELDS, default_column=QuestionnaireModel.questionnaire_id, default_desc=True
            )
            rows, total = await self._execute_paginated(
                session, base, count_base,
                sort_column=sort_column, sort_desc=sort_desc,
                limit=limit, offset=offset, total_mode=total_mode,
            )
        logger.debug(
            "Questionnaires listed",
            extra={
                "event": "questionnaire.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    async def delete(self, questionnaire_id: int) -> bool:
        """`item` is self-referential (parent_item_id, see QuestionnaireModel's
        docstring) with deliberately NO ORM-level parent/children
        `relationship()` declared for it — which means SQLAlchemy's unit-of-
        work has no row-level dependency information for that table and
        cannot order a cascade delete-orphan's per-row DELETEs correctly
        within it, raising `ForeignKeyViolationError` the moment a parent
        item is deleted before a child item that still points at it
        (confirmed live: `session.delete(q)` alone 500s for any
        questionnaire with a nested item tree more than one level deep).
        Pre-delete the whole item/grandchild subtree via the same Core-level
        bulk statements patch_full() uses (one `DELETE ... WHERE
        questionnaire_pk = :id` per table — no self-referential ordering
        concern at all, since every row in `questionnaire_item` already
        carries `questionnaire_pk` denormalized straight to this row) before
        letting the ORM cascade handle every other (non-recursive, two-level
        child/grandchild) sub-resource normally."""
        async with self.session_factory() as session:
            stmt = select(QuestionnaireModel).where(QuestionnaireModel.questionnaire_id == questionnaire_id)
            q = (await session.execute(stmt)).scalars().first()
            if not q:
                return False
            try:
                item_ids_subq = select(QuestionnaireItem.id).where(QuestionnaireItem.questionnaire_pk == q.id)
                await session.execute(
                    sa_delete(QuestionnaireItemCoding).where(QuestionnaireItemCoding.questionnaire_item_id.in_(item_ids_subq))
                )
                await session.execute(
                    sa_delete(QuestionnaireItemEnableWhen).where(QuestionnaireItemEnableWhen.questionnaire_item_id.in_(item_ids_subq))
                )
                await session.execute(
                    sa_delete(QuestionnaireItemAnswerOption).where(QuestionnaireItemAnswerOption.questionnaire_item_id.in_(item_ids_subq))
                )
                await session.execute(
                    sa_delete(QuestionnaireItemInitial).where(QuestionnaireItemInitial.questionnaire_item_id.in_(item_ids_subq))
                )
                await session.execute(sa_delete(QuestionnaireItem).where(QuestionnaireItem.questionnaire_pk == q.id))

                await session.delete(q)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
