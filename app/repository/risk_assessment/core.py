from datetime import date, datetime

from sqlalchemy import delete, func
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_date_range_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.enums import SubjectReferenceType
from app.models.risk_assessment import (
    RiskAssessmentIdentifierModel,
    RiskAssessmentIdentifierTypeCodingModel,
    RiskAssessmentModel,
    RiskAssessmentPredictionModel,
    RiskAssessmentPredOutcomeCodingModel,
    RiskAssessmentPredQualRiskCodingModel,
    RiskAssessmentReasonCodeCodingModel,
    RiskAssessmentReasonCodeModel,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for RiskAssessment."""

    async def get_by_risk_assessment_id(
        self, risk_assessment_id: int
    ) -> RiskAssessmentModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(RiskAssessmentModel).where(
                    RiskAssessmentModel.risk_assessment_id == risk_assessment_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_risk_assessment_id_in_org(
        self, risk_assessment_id: int, org_id: str
    ) -> RiskAssessmentModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(RiskAssessmentModel).where(
                    RiskAssessmentModel.risk_assessment_id == risk_assessment_id,
                    RiskAssessmentModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def risk_assessment_belongs_to_org(
        self, risk_assessment_id: int, org_id: str
    ) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(RiskAssessmentModel.id)).where(
                RiskAssessmentModel.risk_assessment_id == risk_assessment_id,
                RiskAssessmentModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        status: str | None = None,
        subject: str | None = None,
        condition: str | None = None,
        performer: str | None = None,
        occurrence: date | datetime | str | None = None,
        identifier: str | None = None,
    ):
        stmt = stmt.where(RiskAssessmentModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, RiskAssessmentModel.status, status)

        if subject:
            subj_type, subj_id = parse_reference(subject, SubjectReferenceType)
            if subj_type:
                stmt = stmt.where(RiskAssessmentModel.subject_type == subj_type)
            if subj_id:
                stmt = stmt.where(RiskAssessmentModel.subject_id == subj_id)

        if condition:
            parts = condition.split("/")
            if len(parts) == 2 and parts[1].isdigit():
                stmt = stmt.where(RiskAssessmentModel.condition_id == int(parts[1]))
            elif condition.isdigit():
                stmt = stmt.where(RiskAssessmentModel.condition_id == int(condition))

        if performer:
            parts = performer.split("/")
            if len(parts) == 2 and parts[1].isdigit():
                stmt = stmt.where(RiskAssessmentModel.performer_id == int(parts[1]))
            elif performer.isdigit():
                stmt = stmt.where(RiskAssessmentModel.performer_id == int(performer))

        if occurrence:
            stmt = apply_date_range_filter(
                stmt, RiskAssessmentModel.occurrence_date_time, occurrence
            )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                RiskAssessmentIdentifierModel,
                RiskAssessmentIdentifierModel.risk_assessment_pk == RiskAssessmentModel.id,
                RiskAssessmentIdentifierModel.system,
                RiskAssessmentIdentifierModel.value,
                identifier,
            )

        return stmt

    async def list(
        self,
        org_id: str,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
        status: str | None = None,
        subject: str | None = None,
        condition: str | None = None,
        performer: str | None = None,
        occurrence: date | datetime | str | None = None,
        identifier: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[RiskAssessmentModel], int]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(RiskAssessmentModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                status=status,
                subject=subject,
                condition=condition,
                performer=performer,
                occurrence=occurrence,
                identifier=identifier,
            )

            data_stmt = select(RiskAssessmentModel)
            data_stmt = self._apply_list_filters(
                data_stmt,
                org_id=org_id,
                status=status,
                subject=subject,
                condition=condition,
                performer=performer,
                occurrence=occurrence,
                identifier=identifier,
            )
            data_stmt = _with_relationships(data_stmt)

            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                RiskAssessmentModel.risk_assessment_id,
                default_desc=True,
            )

            rows, total = await self._execute_paginated(
                session,
                data_stmt,
                count_stmt,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
            return list(rows), total or 0

    async def delete(self, risk_assessment_id: int, org_id: str) -> bool:
        """Deletes a RiskAssessment resource if it belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(RiskAssessmentModel).where(
                RiskAssessmentModel.risk_assessment_id == risk_assessment_id,
                RiskAssessmentModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False

            # Delete grandchildren
            pred_ids = (
                await session.execute(
                    select(RiskAssessmentPredictionModel.id).where(
                        RiskAssessmentPredictionModel.risk_assessment_pk == model.id
                    )
                )
            ).scalars().all()
            if pred_ids:
                await session.execute(
                    delete(RiskAssessmentPredOutcomeCodingModel).where(
                        RiskAssessmentPredOutcomeCodingModel.risk_assessment_prediction_id.in_(pred_ids)
                    )
                )
                await session.execute(
                    delete(RiskAssessmentPredQualRiskCodingModel).where(
                        RiskAssessmentPredQualRiskCodingModel.risk_assessment_prediction_id.in_(pred_ids)
                    )
                )

            rc_ids = (
                await session.execute(
                    select(RiskAssessmentReasonCodeModel.id).where(
                        RiskAssessmentReasonCodeModel.risk_assessment_pk == model.id
                    )
                )
            ).scalars().all()
            if rc_ids:
                await session.execute(
                    delete(RiskAssessmentReasonCodeCodingModel).where(
                        RiskAssessmentReasonCodeCodingModel.risk_assessment_reason_code_id.in_(rc_ids)
                    )
                )

            id_ids = (
                await session.execute(
                    select(RiskAssessmentIdentifierModel.id).where(
                        RiskAssessmentIdentifierModel.risk_assessment_pk == model.id
                    )
                )
            ).scalars().all()
            if id_ids:
                await session.execute(
                    delete(RiskAssessmentIdentifierTypeCodingModel).where(
                        RiskAssessmentIdentifierTypeCodingModel.risk_assessment_identifier_id.in_(id_ids)
                    )
                )

            await session.delete(model)
            await session.commit()
            return True
