from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.observation import (
    ObservationIdentifier,
    ObservationModel,
    ObservationStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the Observation parent row (no sub-resources).
    Default (gateway-trusted) pattern — same as QuestionnaireResponse/
    ServiceRequest/MedicationRequest: no org-scoped existence check or
    ownership enforcement here at all."""

    async def get_by_observation_id(self, observation_id: int) -> ObservationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ObservationModel).where(ObservationModel.observation_id == observation_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_observation_id_in_org(
        self, observation_id: int, org_id: str
    ) -> ObservationModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ObservationModel).where(
                    ObservationModel.observation_id == observation_id,
                    ObservationModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def observation_belongs_to_org(self, observation_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(ObservationModel.id).where(
                ObservationModel.observation_id == observation_id,
                ObservationModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        user_id: str | None = None,
        status: ObservationStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(ObservationModel.tenant_id == org_id)
        if user_id:
            stmt = stmt.where(ObservationModel.user_id == user_id)
        stmt = apply_token_filter(stmt, ObservationModel.status, status)
        if subject:
            stmt = stmt.where(ObservationModel.subject_reference == subject)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(ObservationIdentifier.id).where(
                    ObservationIdentifier.observation_pk == ObservationModel.id,
                    ObservationIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        status: ObservationStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ObservationModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "user_id": user_id,
                "status": status,
                "subject": subject,
                "identifier": identifier,
            }
            base = self._apply_list_filters(_with_relationships(select(ObservationModel)), **filter_kwargs)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(ObservationModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort, _SORTABLE_FIELDS, default_column=ObservationModel.observation_id, default_desc=True
            )
            rows, total = await self._execute_paginated(
                session, base, count_base, sort_column=sort_column, sort_desc=sort_desc,
                limit=limit, offset=offset, total_mode=total_mode,
            )
        logger.debug(
            "Observations listed",
            extra={
                "event": "observation.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    async def get_me(
        self,
        user_id: str,
        org_id: str | None = None,
        status: ObservationStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ObservationModel], int | None]:
        return await self.list(
            org_id=org_id, user_id=user_id, status=status,
            subject=subject, identifier=identifier, limit=limit, offset=offset,
            sort=sort, total_mode=total_mode,
        )

    async def delete(self, observation_id: int) -> bool:
        """Every sub-resource here is a plain two/three-level
        child/grandchild (no self-referential or mutual-recursion gotcha
        like Questionnaire's item/answer), so a plain ORM
        `session.delete()` with every relationship's own
        `cascade="all, delete-orphan"` is safe and sufficient."""
        async with self.session_factory() as session:
            stmt = select(ObservationModel).where(ObservationModel.observation_id == observation_id)
            obs = (await session.execute(stmt)).scalars().first()
            if not obs:
                return False
            try:
                await session.delete(obs)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
