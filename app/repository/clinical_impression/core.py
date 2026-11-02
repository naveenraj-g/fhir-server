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
from app.models.clinical_impression import (
    ClinicalImpressionAssessorReferenceType,
    ClinicalImpressionFindingItemCodingModel,
    ClinicalImpressionFindingModel,
    ClinicalImpressionIdentifierModel,
    ClinicalImpressionIdentifierTypeCodingModel,
    ClinicalImpressionInvestigationCodeCodingModel,
    ClinicalImpressionInvestigationItemModel,
    ClinicalImpressionInvestigationModel,
    ClinicalImpressionModel,
    ClinicalImpressionNoteModel,
    ClinicalImpressionProblemModel,
    ClinicalImpressionPrognosisCodeableConceptModel,
    ClinicalImpressionPrognosisCodingModel,
    ClinicalImpressionPrognosisReferenceModel,
    ClinicalImpressionProtocolModel,
    ClinicalImpressionSupportingInfoModel,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for ClinicalImpression."""

    async def get_by_clinical_impression_id(
        self, clinical_impression_id: int
    ) -> ClinicalImpressionModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ClinicalImpressionModel).where(
                    ClinicalImpressionModel.clinical_impression_id == clinical_impression_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_clinical_impression_id_in_org(
        self, clinical_impression_id: int, org_id: str
    ) -> ClinicalImpressionModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ClinicalImpressionModel).where(
                    ClinicalImpressionModel.clinical_impression_id == clinical_impression_id,
                    ClinicalImpressionModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def clinical_impression_belongs_to_org(
        self, clinical_impression_id: int, org_id: str
    ) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(ClinicalImpressionModel.id)).where(
                ClinicalImpressionModel.clinical_impression_id == clinical_impression_id,
                ClinicalImpressionModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        status: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        assessor: str | None = None,
        date_val: date | datetime | str | None = None,
        identifier: str | None = None,
    ):
        stmt = stmt.where(ClinicalImpressionModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, ClinicalImpressionModel.status, status)

        if subject:
            subj_type, subj_id = parse_reference(subject, SubjectReferenceType)
            if subj_type:
                stmt = stmt.where(ClinicalImpressionModel.subject_type == subj_type)
            if subj_id:
                stmt = stmt.where(ClinicalImpressionModel.subject_id == subj_id)

        if encounter:
            parts = encounter.split("/")
            if len(parts) == 2 and parts[1].isdigit():
                stmt = stmt.where(ClinicalImpressionModel.encounter_id == int(parts[1]))
            elif encounter.isdigit():
                stmt = stmt.where(ClinicalImpressionModel.encounter_id == int(encounter))

        if assessor:
            ass_type, ass_id = parse_reference(assessor, ClinicalImpressionAssessorReferenceType)
            if ass_type:
                stmt = stmt.where(ClinicalImpressionModel.assessor_type == ass_type)
            if ass_id:
                stmt = stmt.where(ClinicalImpressionModel.assessor_id == ass_id)
            elif "/" in assessor:
                parts = assessor.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    stmt = stmt.where(ClinicalImpressionModel.assessor_id == int(parts[1]))
            elif assessor.isdigit():
                stmt = stmt.where(ClinicalImpressionModel.assessor_id == int(assessor))

        if date_val:
            stmt = apply_date_range_filter(stmt, ClinicalImpressionModel.date, date_val)

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                ClinicalImpressionIdentifierModel,
                ClinicalImpressionIdentifierModel.clinical_impression_pk == ClinicalImpressionModel.id,
                ClinicalImpressionIdentifierModel.system,
                ClinicalImpressionIdentifierModel.value,
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
        encounter: str | None = None,
        assessor: str | None = None,
        date_val: date | datetime | str | None = None,
        identifier: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ClinicalImpressionModel], int]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(ClinicalImpressionModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                status=status,
                subject=subject,
                encounter=encounter,
                assessor=assessor,
                date_val=date_val,
                identifier=identifier,
            )

            data_stmt = select(ClinicalImpressionModel)
            data_stmt = self._apply_list_filters(
                data_stmt,
                org_id=org_id,
                status=status,
                subject=subject,
                encounter=encounter,
                assessor=assessor,
                date_val=date_val,
                identifier=identifier,
            )
            data_stmt = _with_relationships(data_stmt)

            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                ClinicalImpressionModel.clinical_impression_id,
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

    async def delete(self, clinical_impression_id: int, org_id: str) -> bool:
        """Deletes a ClinicalImpression resource if it belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(ClinicalImpressionModel).where(
                ClinicalImpressionModel.clinical_impression_id == clinical_impression_id,
                ClinicalImpressionModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False

            # Delete grandchildren
            inv_ids = (
                await session.execute(
                    select(ClinicalImpressionInvestigationModel.id).where(
                        ClinicalImpressionInvestigationModel.clinical_impression_pk == model.id
                    )
                )
            ).scalars().all()
            if inv_ids:
                await session.execute(
                    delete(ClinicalImpressionInvestigationCodeCodingModel).where(
                        ClinicalImpressionInvestigationCodeCodingModel.clinical_impression_investigation_id.in_(inv_ids)
                    )
                )
                await session.execute(
                    delete(ClinicalImpressionInvestigationItemModel).where(
                        ClinicalImpressionInvestigationItemModel.clinical_impression_investigation_id.in_(inv_ids)
                    )
                )

            find_ids = (
                await session.execute(
                    select(ClinicalImpressionFindingModel.id).where(
                        ClinicalImpressionFindingModel.clinical_impression_pk == model.id
                    )
                )
            ).scalars().all()
            if find_ids:
                await session.execute(
                    delete(ClinicalImpressionFindingItemCodingModel).where(
                        ClinicalImpressionFindingItemCodingModel.clinical_impression_finding_id.in_(find_ids)
                    )
                )

            id_ids = (
                await session.execute(
                    select(ClinicalImpressionIdentifierModel.id).where(
                        ClinicalImpressionIdentifierModel.clinical_impression_pk == model.id
                    )
                )
            ).scalars().all()
            if id_ids:
                await session.execute(
                    delete(ClinicalImpressionIdentifierTypeCodingModel).where(
                        ClinicalImpressionIdentifierTypeCodingModel.clinical_impression_identifier_id.in_(id_ids)
                    )
                )

            prog_cc_ids = (
                await session.execute(
                    select(ClinicalImpressionPrognosisCodeableConceptModel.id).where(
                        ClinicalImpressionPrognosisCodeableConceptModel.clinical_impression_pk == model.id
                    )
                )
            ).scalars().all()
            if prog_cc_ids:
                await session.execute(
                    delete(ClinicalImpressionPrognosisCodingModel).where(
                        ClinicalImpressionPrognosisCodingModel.clinical_impression_prognosis_id.in_(prog_cc_ids)
                    )
                )

            await session.delete(model)
            await session.commit()
            return True
