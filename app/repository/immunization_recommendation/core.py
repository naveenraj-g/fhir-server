from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_date_range_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.immunization_recommendation import (
    ImmunizationRecommendationIdentifierModel,
    ImmunizationRecommendationModel,
    ImmunizationRecommendationPatientReferenceType,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for ImmunizationRecommendation."""

    async def get_by_immunization_recommendation_id(
        self, immunization_recommendation_id: int
    ) -> ImmunizationRecommendationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationRecommendationModel).where(
                    ImmunizationRecommendationModel.immunization_recommendation_id
                    == immunization_recommendation_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_immunization_recommendation_id_in_org(
        self, immunization_recommendation_id: int, org_id: str
    ) -> ImmunizationRecommendationModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationRecommendationModel).where(
                    ImmunizationRecommendationModel.immunization_recommendation_id
                    == immunization_recommendation_id,
                    ImmunizationRecommendationModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def immunization_recommendation_belongs_to_org(
        self, immunization_recommendation_id: int, org_id: str
    ) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(ImmunizationRecommendationModel.id)).where(
                ImmunizationRecommendationModel.immunization_recommendation_id
                == immunization_recommendation_id,
                ImmunizationRecommendationModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(ImmunizationRecommendationModel.tenant_id == org_id)

        if patient:
            if patient.isdigit():
                stmt = stmt.where(ImmunizationRecommendationModel.patient_id == int(patient))
            else:
                p_type, p_id = parse_reference(patient, ImmunizationRecommendationPatientReferenceType)
                if p_id:
                    stmt = stmt.where(ImmunizationRecommendationModel.patient_id == p_id)
                else:
                    stmt = stmt.where(ImmunizationRecommendationModel.patient_reference == patient)

        if date_val is not None or date_from is not None or date_to is not None:
            stmt = apply_date_range_filter(
                stmt,
                ImmunizationRecommendationModel.date,
                date_val,
                date_from,
                date_to,
            )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                ImmunizationRecommendationIdentifierModel,
                ImmunizationRecommendationIdentifierModel.immunization_recommendation_pk
                == ImmunizationRecommendationModel.id,
                lambda s: apply_token_filter(
                    s,
                    ImmunizationRecommendationIdentifierModel.system,
                    ImmunizationRecommendationIdentifierModel.value,
                    identifier,
                ),
            )

        return stmt

    async def list(
        self,
        *,
        org_id: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        identifier: str | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ImmunizationRecommendationModel], int | None]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(ImmunizationRecommendationModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                patient=patient,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
                identifier=identifier,
            )
            total = (await session.execute(count_stmt)).scalar() if total_mode == "accurate" else None

            stmt = select(ImmunizationRecommendationModel)
            stmt = self._apply_list_filters(
                stmt,
                org_id=org_id,
                patient=patient,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
                identifier=identifier,
            )
            stmt = _with_relationships(stmt)
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                ImmunizationRecommendationModel.immunization_recommendation_id,
                default_desc=False,
            )
            rows, total = await self._execute_paginated(
                session,
                stmt,
                count_stmt,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
            return list(rows), total

    async def delete(self, immunization_recommendation_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(ImmunizationRecommendationModel).where(
                ImmunizationRecommendationModel.immunization_recommendation_id == immunization_recommendation_id,
                ImmunizationRecommendationModel.tenant_id == org_id,
            )
            row = (await session.execute(stmt)).scalars().first()
            if not row:
                return False
            await session.delete(row)
            await session.commit()
            return True
