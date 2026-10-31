from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.episode_of_care import (
    EpisodeOfCareIdentifier,
    EpisodeOfCareModel,
    EpisodeOfCareType,
    EpisodeOfCareTypeCoding,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_care_manager_ref,
    _parse_managing_org_ref,
    _parse_patient_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for EpisodeOfCare."""

    async def get_by_episode_of_care_id(
        self, episode_of_care_id: int
    ) -> EpisodeOfCareModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EpisodeOfCareModel).where(
                    EpisodeOfCareModel.episode_of_care_id == episode_of_care_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_episode_of_care_id_in_org(
        self, episode_of_care_id: int, org_id: str
    ) -> EpisodeOfCareModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EpisodeOfCareModel).where(
                    EpisodeOfCareModel.episode_of_care_id == episode_of_care_id,
                    EpisodeOfCareModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def episode_of_care_belongs_to_org(
        self, episode_of_care_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(EpisodeOfCareModel.id).where(
                EpisodeOfCareModel.episode_of_care_id == episode_of_care_id,
                EpisodeOfCareModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | None = None,
        patient: str | None = None,
        type: str | None = None,
        care_manager: str | None = None,
        organization: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(EpisodeOfCareModel.tenant_id == org_id)
        if status:
            stmt = stmt.where(EpisodeOfCareModel.status == status)
        if patient:
            p_type, p_id = _parse_patient_ref(patient)
            if p_id:
                stmt = stmt.where(EpisodeOfCareModel.patient_id == p_id)
                if p_type:
                    stmt = stmt.where(EpisodeOfCareModel.patient_type == p_type)
            else:
                stmt = stmt.where(EpisodeOfCareModel.patient_reference == patient)
        if type:
            stmt = apply_child_exists_filter(
                stmt,
                select(EpisodeOfCareTypeCoding.id)
                .join(
                    EpisodeOfCareType,
                    EpisodeOfCareTypeCoding.type_id == EpisodeOfCareType.id,
                )
                .where(
                    EpisodeOfCareType.episode_of_care_pk == EpisodeOfCareModel.id,
                    EpisodeOfCareTypeCoding.code == type,
                ),
            )
        if care_manager:
            cm_type, cm_id = _parse_care_manager_ref(care_manager)
            if cm_id:
                stmt = stmt.where(EpisodeOfCareModel.care_manager_id == cm_id)
                if cm_type:
                    stmt = stmt.where(EpisodeOfCareModel.care_manager_type == cm_type)
            else:
                stmt = stmt.where(EpisodeOfCareModel.care_manager_reference == care_manager)
        if organization:
            org_type, org_id_val = _parse_managing_org_ref(organization)
            if org_id_val:
                stmt = stmt.where(EpisodeOfCareModel.managing_organization_id == org_id_val)
                if org_type:
                    stmt = stmt.where(
                        EpisodeOfCareModel.managing_organization_type == org_type
                    )
            else:
                stmt = stmt.where(
                    EpisodeOfCareModel.managing_organization_reference == organization
                )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(EpisodeOfCareIdentifier.id).where(
                    EpisodeOfCareIdentifier.episode_of_care_pk == EpisodeOfCareModel.id,
                    EpisodeOfCareIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str,
        status: str | None = None,
        patient: str | None = None,
        type: str | None = None,
        care_manager: str | None = None,
        organization: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[EpisodeOfCareModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "patient": patient,
                "type": type,
                "care_manager": care_manager,
                "organization": organization,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(EpisodeOfCareModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(EpisodeOfCareModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=EpisodeOfCareModel.episode_of_care_id,
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

    async def delete(self, episode_of_care_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(EpisodeOfCareModel).where(
                EpisodeOfCareModel.episode_of_care_id == episode_of_care_id
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True
