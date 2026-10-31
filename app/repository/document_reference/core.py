from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.document_reference import (
    DocumentReferenceAuthor,
    DocumentReferenceCategory,
    DocumentReferenceCategoryCoding,
    DocumentReferenceIdentifier,
    DocumentReferenceModel,
    DocumentReferenceRelatesTo,
    DocumentReferenceTypeCoding,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for DocumentReference."""

    async def get_by_document_reference_id(self, document_reference_id: int) -> DocumentReferenceModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(DocumentReferenceModel).where(DocumentReferenceModel.document_reference_id == document_reference_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_document_reference_id_in_org(
        self, document_reference_id: int, org_id: str
    ) -> DocumentReferenceModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(DocumentReferenceModel).where(
                    DocumentReferenceModel.document_reference_id == document_reference_id,
                    DocumentReferenceModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def document_reference_belongs_to_org(self, document_reference_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(DocumentReferenceModel.id).where(
                DocumentReferenceModel.document_reference_id == document_reference_id,
                DocumentReferenceModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | None = None,
        doc_status: str | None = None,
        type: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        author: str | None = None,
        custodian: str | None = None,
        authenticator: str | None = None,
        relates_to: str | None = None,
        identifier: str | None = None,
        description: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(DocumentReferenceModel.tenant_id == org_id)
        if status:
            stmt = stmt.where(DocumentReferenceModel.status == status)
        if doc_status:
            stmt = stmt.where(DocumentReferenceModel.doc_status == doc_status)
        if type:
            stmt = apply_child_exists_filter(
                stmt,
                select(DocumentReferenceTypeCoding.id).where(
                    DocumentReferenceTypeCoding.document_reference_pk == DocumentReferenceModel.id,
                    DocumentReferenceTypeCoding.code == type,
                ),
            )
        if category:
            stmt = apply_child_exists_filter(
                stmt,
                select(DocumentReferenceCategoryCoding.id)
                .join(
                    DocumentReferenceCategory,
                    DocumentReferenceCategoryCoding.document_reference_category_id == DocumentReferenceCategory.id,
                )
                .where(
                    DocumentReferenceCategory.document_reference_pk == DocumentReferenceModel.id,
                    DocumentReferenceCategoryCoding.code == category,
                ),
            )
        if subject:
            if subject.isdigit():
                stmt = stmt.where(DocumentReferenceModel.subject_id == int(subject))
            else:
                stmt = stmt.where(DocumentReferenceModel.subject_reference == subject)
        if author:
            if author.isdigit():
                stmt = apply_child_exists_filter(
                    stmt,
                    select(DocumentReferenceAuthor.id).where(
                        DocumentReferenceAuthor.document_reference_pk == DocumentReferenceModel.id,
                        DocumentReferenceAuthor.author_id == int(author),
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(DocumentReferenceAuthor.id).where(
                        DocumentReferenceAuthor.document_reference_pk == DocumentReferenceModel.id,
                        DocumentReferenceAuthor.author_reference == author,
                    ),
                )
        if custodian:
            if custodian.isdigit():
                stmt = stmt.where(DocumentReferenceModel.custodian_id == int(custodian))
            else:
                stmt = stmt.where(DocumentReferenceModel.custodian_reference == custodian)
        if authenticator:
            if authenticator.isdigit():
                stmt = stmt.where(DocumentReferenceModel.authenticator_id == int(authenticator))
            else:
                stmt = stmt.where(DocumentReferenceModel.authenticator_reference == authenticator)
        if relates_to:
            if relates_to.isdigit():
                stmt = apply_child_exists_filter(
                    stmt,
                    select(DocumentReferenceRelatesTo.id).where(
                        DocumentReferenceRelatesTo.document_reference_pk == DocumentReferenceModel.id,
                        DocumentReferenceRelatesTo.target_id == int(relates_to),
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(DocumentReferenceRelatesTo.id).where(
                        DocumentReferenceRelatesTo.document_reference_pk == DocumentReferenceModel.id,
                        DocumentReferenceRelatesTo.target_reference == relates_to,
                    ),
                )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(DocumentReferenceIdentifier.id).where(
                    DocumentReferenceIdentifier.document_reference_pk == DocumentReferenceModel.id,
                    DocumentReferenceIdentifier.value == identifier,
                ),
            )
        if description:
            stmt = stmt.where(DocumentReferenceModel.description.ilike(f"%{description}%"))

        return stmt

    async def list(
        self,
        org_id: str,
        status: str | None = None,
        doc_status: str | None = None,
        type: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        author: str | None = None,
        custodian: str | None = None,
        authenticator: str | None = None,
        relates_to: str | None = None,
        identifier: str | None = None,
        description: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[DocumentReferenceModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "doc_status": doc_status,
                "type": type,
                "category": category,
                "subject": subject,
                "author": author,
                "custodian": custodian,
                "authenticator": authenticator,
                "relates_to": relates_to,
                "identifier": identifier,
                "description": description,
            }
            base = self._apply_list_filters(
                _with_relationships(select(DocumentReferenceModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(DocumentReferenceModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=DocumentReferenceModel.document_reference_id,
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

    async def delete(self, document_reference_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(DocumentReferenceModel).where(DocumentReferenceModel.document_reference_id == document_reference_id)
            doc_ref = (await session.execute(stmt)).scalars().first()
            if not doc_ref:
                return False
            await session.delete(doc_ref)
            await session.commit()
            return True
