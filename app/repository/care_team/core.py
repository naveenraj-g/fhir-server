from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.care_team import (
    CareTeamCategory,
    CareTeamCategoryCoding,
    CareTeamIdentifier,
    CareTeamModel,
    CareTeamParticipant,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_encounter_ref,
    _parse_member_ref,
    _parse_subject_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for CareTeam."""

    async def get_by_care_team_id(self, care_team_id: int) -> CareTeamModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(CareTeamModel).where(CareTeamModel.care_team_id == care_team_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_care_team_id_in_org(
        self, care_team_id: int, org_id: str
    ) -> CareTeamModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(CareTeamModel).where(
                    CareTeamModel.care_team_id == care_team_id,
                    CareTeamModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def care_team_belongs_to_org(self, care_team_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(CareTeamModel.id).where(
                CareTeamModel.care_team_id == care_team_id,
                CareTeamModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | None = None,
        name: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        participant: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(CareTeamModel.tenant_id == org_id)
        if status:
            stmt = stmt.where(CareTeamModel.status == status)
        if name:
            stmt = stmt.where(CareTeamModel.name.ilike(f"%{name}%"))
        if category:
            stmt = apply_child_exists_filter(
                stmt,
                select(CareTeamCategoryCoding.id)
                .join(
                    CareTeamCategory,
                    CareTeamCategoryCoding.category_id == CareTeamCategory.id,
                )
                .where(
                    CareTeamCategory.care_team_pk == CareTeamModel.id,
                    CareTeamCategoryCoding.code == category,
                ),
            )
        if subject:
            s_type, s_id = _parse_subject_ref(subject)
            if s_id:
                stmt = stmt.where(CareTeamModel.subject_id == s_id)
                if s_type:
                    stmt = stmt.where(CareTeamModel.subject_type == s_type)
            else:
                stmt = stmt.where(CareTeamModel.subject_reference == subject)
        if encounter:
            e_type, e_id = _parse_encounter_ref(encounter)
            if e_id:
                stmt = stmt.where(CareTeamModel.encounter_id == e_id)
            else:
                stmt = stmt.where(CareTeamModel.encounter_reference == encounter)
        if participant:
            m_type, m_id = _parse_member_ref(participant)
            if m_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CareTeamParticipant.id).where(
                        CareTeamParticipant.care_team_pk == CareTeamModel.id,
                        CareTeamParticipant.member_id == m_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CareTeamParticipant.id).where(
                        CareTeamParticipant.care_team_pk == CareTeamModel.id,
                        CareTeamParticipant.member_reference == participant,
                    ),
                )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(CareTeamIdentifier.id).where(
                    CareTeamIdentifier.care_team_pk == CareTeamModel.id,
                    CareTeamIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str,
        status: str | None = None,
        name: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        participant: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[CareTeamModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "name": name,
                "category": category,
                "subject": subject,
                "encounter": encounter,
                "participant": participant,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(CareTeamModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(CareTeamModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=CareTeamModel.care_team_id,
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

    async def delete(self, care_team_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(CareTeamModel).where(CareTeamModel.care_team_id == care_team_id)
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True
