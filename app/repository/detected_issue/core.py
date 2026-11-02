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
from app.models.detected_issue import (
    DetectedIssueAuthorReferenceType,
    DetectedIssueCodeCodingModel,
    DetectedIssueEvidenceCodeCodingModel,
    DetectedIssueEvidenceCodeModel,
    DetectedIssueEvidenceDetailModel,
    DetectedIssueEvidenceModel,
    DetectedIssueIdentifierModel,
    DetectedIssueIdentifierTypeCodingModel,
    DetectedIssueMitigationActionCodingModel,
    DetectedIssueMitigationModel,
    DetectedIssueModel,
    DetectedIssuePatientReferenceType,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for DetectedIssue."""

    async def get_by_detected_issue_id(
        self, detected_issue_id: int
    ) -> DetectedIssueModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(DetectedIssueModel).where(
                    DetectedIssueModel.detected_issue_id == detected_issue_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_detected_issue_id_in_org(
        self, detected_issue_id: int, org_id: str
    ) -> DetectedIssueModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(DetectedIssueModel).where(
                    DetectedIssueModel.detected_issue_id == detected_issue_id,
                    DetectedIssueModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def detected_issue_belongs_to_org(
        self, detected_issue_id: int, org_id: str
    ) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(DetectedIssueModel.id)).where(
                DetectedIssueModel.detected_issue_id == detected_issue_id,
                DetectedIssueModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        status: str | None = None,
        patient: str | None = None,
        author: str | None = None,
        identified: date | datetime | str | None = None,
        identifier: str | None = None,
        code: str | None = None,
    ):
        stmt = stmt.where(DetectedIssueModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, DetectedIssueModel.status, status)

        if patient:
            p_type, p_id = parse_reference(patient, DetectedIssuePatientReferenceType)
            if p_type:
                stmt = stmt.where(DetectedIssueModel.patient_type == p_type)
            if p_id:
                stmt = stmt.where(DetectedIssueModel.patient_id == p_id)
            elif "/" in patient:
                parts = patient.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    stmt = stmt.where(DetectedIssueModel.patient_id == int(parts[1]))
            elif patient.isdigit():
                stmt = stmt.where(DetectedIssueModel.patient_id == int(patient))

        if author:
            a_type, a_id = parse_reference(author, DetectedIssueAuthorReferenceType)
            if a_type:
                stmt = stmt.where(DetectedIssueModel.author_type == a_type)
            if a_id:
                stmt = stmt.where(DetectedIssueModel.author_id == a_id)
            elif "/" in author:
                parts = author.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    stmt = stmt.where(DetectedIssueModel.author_id == int(parts[1]))
            elif author.isdigit():
                stmt = stmt.where(DetectedIssueModel.author_id == int(author))

        if identified:
            stmt = apply_date_range_filter(
                stmt, DetectedIssueModel.identified_date_time, identified
            )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                DetectedIssueIdentifierModel,
                DetectedIssueIdentifierModel.detected_issue_pk == DetectedIssueModel.id,
                DetectedIssueIdentifierModel.system,
                DetectedIssueIdentifierModel.value,
                identifier,
            )

        if code:
            stmt = apply_child_exists_filter(
                stmt,
                DetectedIssueCodeCodingModel,
                DetectedIssueCodeCodingModel.detected_issue_pk == DetectedIssueModel.id,
                DetectedIssueCodeCodingModel.system,
                DetectedIssueCodeCodingModel.code,
                code,
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
        author: str | None = None,
        identified: date | datetime | str | None = None,
        identifier: str | None = None,
        code: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[DetectedIssueModel], int]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(DetectedIssueModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                status=status,
                patient=patient,
                author=author,
                identified=identified,
                identifier=identifier,
                code=code,
            )

            data_stmt = select(DetectedIssueModel)
            data_stmt = self._apply_list_filters(
                data_stmt,
                org_id=org_id,
                status=status,
                patient=patient,
                author=author,
                identified=identified,
                identifier=identifier,
                code=code,
            )
            data_stmt = _with_relationships(data_stmt)

            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                DetectedIssueModel.detected_issue_id,
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

    async def delete(self, detected_issue_id: int, org_id: str) -> bool:
        """Deletes a DetectedIssue resource if it belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(DetectedIssueModel).where(
                    DetectedIssueModel.detected_issue_id == detected_issue_id,
                    DetectedIssueModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False

            await session.delete(model)
            await session.commit()
            return True
