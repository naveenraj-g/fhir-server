from sqlalchemy import delete as sa_delete, func
from sqlalchemy.future import select

from app.core.filters import apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.questionnaire_response import (
    QuestionnaireResponseAnswer,
    QuestionnaireResponseBasedOn,
    QuestionnaireResponseIdentifierTypeCoding,
    QuestionnaireResponseItem,
    QuestionnaireResponseModel,
    QuestionnaireResponsePartOf,
    QuestionnaireResponseStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the QuestionnaireResponse parent row (no sub-resources).

    Default (gateway-trusted) pattern — unlike every currently-built,
    auth-rolled-out resource, there is no org-scoped existence check or
    ownership enforcement here at all: `get_by_questionnaire_response_id()`
    loads by public ID with no filter beyond that, and `list()`
    takes `tenant_id`/`user_id` as plain, optional filter parameters, never
    derived from a verified token."""

    async def get_by_questionnaire_response_id(
        self, questionnaire_response_id: int
    ) -> QuestionnaireResponseModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireResponseModel).where(
                    QuestionnaireResponseModel.questionnaire_response_id == questionnaire_response_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_questionnaire_response_id_in_org(
        self, questionnaire_response_id: int, org_id: str
    ) -> QuestionnaireResponseModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireResponseModel).where(
                    QuestionnaireResponseModel.questionnaire_response_id == questionnaire_response_id,
                    QuestionnaireResponseModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def questionnaire_response_belongs_to_org(
        self, questionnaire_response_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(QuestionnaireResponseModel.id).where(
                QuestionnaireResponseModel.questionnaire_response_id == questionnaire_response_id,
                QuestionnaireResponseModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: QuestionnaireResponseStatus | None = None,
        questionnaire: str | None = None,
        subject: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(QuestionnaireResponseModel.tenant_id == org_id)
        stmt = apply_token_filter(stmt, QuestionnaireResponseModel.status, status)
        if questionnaire:
            stmt = stmt.where(QuestionnaireResponseModel.questionnaire == questionnaire)
        if subject:
            stmt = stmt.where(QuestionnaireResponseModel.subject_reference == subject)
        if identifier:
            stmt = stmt.where(QuestionnaireResponseModel.identifier_value == identifier)
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: QuestionnaireResponseStatus | None = None,
        questionnaire: str | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[QuestionnaireResponseModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "questionnaire": questionnaire,
                "subject": subject,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(QuestionnaireResponseModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(QuestionnaireResponseModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=QuestionnaireResponseModel.questionnaire_response_id,
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
            "QuestionnaireResponses listed",
            extra={
                "event": "questionnaire_response.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    async def delete(self, questionnaire_response_id: int) -> bool:
        """`item` is self-referential (`parent_item_id`) and mutually
        cross-referenced with `answer` (`item.parent_answer_id` ->
        `answer.id`, deliberately NOT a real FK; `answer.item_id` ->
        `item.id`, a real FK — see QuestionnaireResponseItem's own
        docstring for why). Plain ORM `session.delete(qr)` would have no
        row-level dependency information for either relationship and
        cannot order the cascade's per-row DELETEs correctly, so — same
        fix as app.repository.questionnaire.core._CoreMixin.delete() —
        pre-delete the whole item/answer subtree via explicit Core-level
        bulk statements (answer before item, since answer.item_id still
        points at rows about to be deleted) before letting the ORM
        cascade handle every other (non-recursive) sub-resource normally."""
        async with self.session_factory() as session:
            stmt = select(QuestionnaireResponseModel).where(
                QuestionnaireResponseModel.questionnaire_response_id == questionnaire_response_id
            )
            qr = (await session.execute(stmt)).scalars().first()
            if not qr:
                return False
            try:
                await session.execute(
                    sa_delete(QuestionnaireResponseAnswer).where(
                        QuestionnaireResponseAnswer.questionnaire_response_pk == qr.id
                    )
                )
                await session.execute(
                    sa_delete(QuestionnaireResponseItem).where(
                        QuestionnaireResponseItem.questionnaire_response_pk == qr.id
                    )
                )
                await session.execute(
                    sa_delete(QuestionnaireResponseBasedOn).where(
                        QuestionnaireResponseBasedOn.questionnaire_response_pk == qr.id
                    )
                )
                await session.execute(
                    sa_delete(QuestionnaireResponsePartOf).where(
                        QuestionnaireResponsePartOf.questionnaire_response_pk == qr.id
                    )
                )
                await session.execute(
                    sa_delete(QuestionnaireResponseIdentifierTypeCoding).where(
                        QuestionnaireResponseIdentifierTypeCoding.questionnaire_response_pk == qr.id
                    )
                )

                await session.delete(qr)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
