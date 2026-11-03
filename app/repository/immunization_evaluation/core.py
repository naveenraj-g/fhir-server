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
from app.models.immunization_evaluation import (
    ImmunizationEvaluationAuthorityReferenceType,
    ImmunizationEvaluationDoseStatusCodingModel,
    ImmunizationEvaluationIdentifierModel,
    ImmunizationEvaluationImmunizationEventReferenceType,
    ImmunizationEvaluationModel,
    ImmunizationEvaluationPatientReferenceType,
    ImmunizationEvaluationTargetDiseaseCodingModel,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for ImmunizationEvaluation."""

    async def get_by_immunization_evaluation_id(
        self, immunization_evaluation_id: int
    ) -> ImmunizationEvaluationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationEvaluationModel).where(
                    ImmunizationEvaluationModel.immunization_evaluation_id
                    == immunization_evaluation_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_immunization_evaluation_id_in_org(
        self, immunization_evaluation_id: int, org_id: str
    ) -> ImmunizationEvaluationModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationEvaluationModel).where(
                    ImmunizationEvaluationModel.immunization_evaluation_id
                    == immunization_evaluation_id,
                    ImmunizationEvaluationModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def immunization_evaluation_belongs_to_org(
        self, immunization_evaluation_id: int, org_id: str
    ) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(ImmunizationEvaluationModel.id)).where(
                ImmunizationEvaluationModel.immunization_evaluation_id
                == immunization_evaluation_id,
                ImmunizationEvaluationModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        status: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | str | None = None,
        authority: str | None = None,
        immunization_event: str | None = None,
        identifier: str | None = None,
        target_disease: str | None = None,
        dose_status: str | None = None,
    ):
        stmt = stmt.where(ImmunizationEvaluationModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, ImmunizationEvaluationModel.status, status)

        if patient:
            p_type, p_id = parse_reference(
                patient, ImmunizationEvaluationPatientReferenceType
            )
            if p_type:
                stmt = stmt.where(ImmunizationEvaluationModel.patient_type == p_type)
            if p_id:
                stmt = stmt.where(ImmunizationEvaluationModel.patient_id == p_id)
            elif "/" in patient:
                parts = patient.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    stmt = stmt.where(
                        ImmunizationEvaluationModel.patient_id == int(parts[1])
                    )
            elif patient.isdigit():
                stmt = stmt.where(ImmunizationEvaluationModel.patient_id == int(patient))

        if date_val:
            stmt = apply_date_range_filter(
                stmt, ImmunizationEvaluationModel.date, date_val
            )

        if authority:
            a_type, a_id = parse_reference(
                authority, ImmunizationEvaluationAuthorityReferenceType
            )
            if a_type:
                stmt = stmt.where(ImmunizationEvaluationModel.authority_type == a_type)
            if a_id:
                stmt = stmt.where(ImmunizationEvaluationModel.authority_id == a_id)
            elif "/" in authority:
                parts = authority.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    stmt = stmt.where(
                        ImmunizationEvaluationModel.authority_id == int(parts[1])
                    )
            elif authority.isdigit():
                stmt = stmt.where(
                    ImmunizationEvaluationModel.authority_id == int(authority)
                )

        if immunization_event:
            ie_type, ie_id = parse_reference(
                immunization_event, ImmunizationEvaluationImmunizationEventReferenceType
            )
            if ie_type:
                stmt = stmt.where(
                    ImmunizationEvaluationModel.immunization_event_type == ie_type
                )
            if ie_id:
                stmt = stmt.where(
                    ImmunizationEvaluationModel.immunization_event_id == ie_id
                )
            elif "/" in immunization_event:
                parts = immunization_event.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    stmt = stmt.where(
                        ImmunizationEvaluationModel.immunization_event_id
                        == int(parts[1])
                    )
            elif immunization_event.isdigit():
                stmt = stmt.where(
                    ImmunizationEvaluationModel.immunization_event_id
                    == int(immunization_event)
                )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                ImmunizationEvaluationIdentifierModel,
                ImmunizationEvaluationIdentifierModel.immunization_evaluation_pk
                == ImmunizationEvaluationModel.id,
                ImmunizationEvaluationIdentifierModel.system,
                ImmunizationEvaluationIdentifierModel.value,
                identifier,
            )

        if target_disease:
            stmt = apply_child_exists_filter(
                stmt,
                ImmunizationEvaluationTargetDiseaseCodingModel,
                ImmunizationEvaluationTargetDiseaseCodingModel.immunization_evaluation_pk
                == ImmunizationEvaluationModel.id,
                ImmunizationEvaluationTargetDiseaseCodingModel.system,
                ImmunizationEvaluationTargetDiseaseCodingModel.code,
                target_disease,
            )

        if dose_status:
            stmt = apply_child_exists_filter(
                stmt,
                ImmunizationEvaluationDoseStatusCodingModel,
                ImmunizationEvaluationDoseStatusCodingModel.immunization_evaluation_pk
                == ImmunizationEvaluationModel.id,
                ImmunizationEvaluationDoseStatusCodingModel.system,
                ImmunizationEvaluationDoseStatusCodingModel.code,
                dose_status,
            )

        return stmt

    async def list(
        self,
        org_id: str,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
        status: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | str | None = None,
        authority: str | None = None,
        immunization_event: str | None = None,
        identifier: str | None = None,
        target_disease: str | None = None,
        dose_status: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ImmunizationEvaluationModel], int]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(ImmunizationEvaluationModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                status=status,
                patient=patient,
                date_val=date_val,
                authority=authority,
                immunization_event=immunization_event,
                identifier=identifier,
                target_disease=target_disease,
                dose_status=dose_status,
            )

            data_stmt = select(ImmunizationEvaluationModel)
            data_stmt = self._apply_list_filters(
                data_stmt,
                org_id=org_id,
                status=status,
                patient=patient,
                date_val=date_val,
                authority=authority,
                immunization_event=immunization_event,
                identifier=identifier,
                target_disease=target_disease,
                dose_status=dose_status,
            )
            data_stmt = _with_relationships(data_stmt)

            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                ImmunizationEvaluationModel.immunization_evaluation_id,
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

    async def delete(self, immunization_evaluation_id: int, org_id: str) -> bool:
        """Deletes an ImmunizationEvaluation resource if it belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationEvaluationModel).where(
                    ImmunizationEvaluationModel.immunization_evaluation_id
                    == immunization_evaluation_id,
                    ImmunizationEvaluationModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False

            await session.delete(model)
            await session.commit()
            return True
