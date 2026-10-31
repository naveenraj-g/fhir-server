from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.specimen import (
    SpecimenIdentifier,
    SpecimenModel,
    SpecimenTypeCoding,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for Specimen."""

    async def get_by_specimen_id(self, specimen_id: int) -> SpecimenModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(SpecimenModel).where(SpecimenModel.specimen_id == specimen_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_specimen_id_in_org(
        self, specimen_id: int, org_id: str
    ) -> SpecimenModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(SpecimenModel).where(
                    SpecimenModel.specimen_id == specimen_id,
                    SpecimenModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def specimen_belongs_to_org(self, specimen_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(SpecimenModel.id).where(
                SpecimenModel.specimen_id == specimen_id,
                SpecimenModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | None = None,
        type: str | None = None,
        subject: str | None = None,
        accession_identifier: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(SpecimenModel.tenant_id == org_id)
        if status:
            stmt = stmt.where(SpecimenModel.status == status)
        if type:
            stmt = apply_child_exists_filter(
                stmt,
                select(SpecimenTypeCoding.id).where(
                    SpecimenTypeCoding.specimen_pk == SpecimenModel.id,
                    SpecimenTypeCoding.code == type,
                ),
            )
        if subject:
            stmt = stmt.where(SpecimenModel.subject_reference == subject)
        if accession_identifier:
            stmt = stmt.where(SpecimenModel.accession_identifier_value == accession_identifier)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(SpecimenIdentifier.id).where(
                    SpecimenIdentifier.specimen_pk == SpecimenModel.id,
                    SpecimenIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: str | None = None,
        type: str | None = None,
        subject: str | None = None,
        accession_identifier: str | None = None,
        identifier: str | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[SpecimenModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "type": type,
                "subject": subject,
                "accession_identifier": accession_identifier,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(SpecimenModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(SpecimenModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=SpecimenModel.specimen_id,
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

    async def delete(self, specimen_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(SpecimenModel).where(SpecimenModel.specimen_id == specimen_id)
            specimen = (await session.execute(stmt)).scalars().first()
            if not specimen:
                return False
            try:
                await session.delete(specimen)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
