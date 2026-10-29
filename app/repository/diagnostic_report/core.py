from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.diagnostic_report import (
    DiagnosticReportIdentifier,
    DiagnosticReportModel,
    DiagnosticReportStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the DiagnosticReport parent row (no sub-resources).
    Default (gateway-trusted) pattern — same as Observation/
    QuestionnaireResponse/ServiceRequest/MedicationRequest: no org-scoped
    existence check or ownership enforcement here at all."""

    async def get_by_diagnostic_report_id(self, diagnostic_report_id: int) -> DiagnosticReportModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(DiagnosticReportModel).where(
                    DiagnosticReportModel.diagnostic_report_id == diagnostic_report_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(
        self,
        stmt,
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: DiagnosticReportStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
    ):
        if tenant_id:
            stmt = stmt.where(DiagnosticReportModel.tenant_id == tenant_id)
        if user_id:
            stmt = stmt.where(DiagnosticReportModel.user_id == user_id)
        stmt = apply_token_filter(stmt, DiagnosticReportModel.status, status)
        if subject:
            stmt = stmt.where(DiagnosticReportModel.subject_reference == subject)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(DiagnosticReportIdentifier.id).where(
                    DiagnosticReportIdentifier.diagnostic_report_pk == DiagnosticReportModel.id,
                    DiagnosticReportIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: DiagnosticReportStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[DiagnosticReportModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "status": status,
                "subject": subject,
                "identifier": identifier,
            }
            base = self._apply_list_filters(_with_relationships(select(DiagnosticReportModel)), **filter_kwargs)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(DiagnosticReportModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort, _SORTABLE_FIELDS, default_column=DiagnosticReportModel.diagnostic_report_id, default_desc=True
            )
            rows, total = await self._execute_paginated(
                session, base, count_base, sort_column=sort_column, sort_desc=sort_desc,
                limit=limit, offset=offset, total_mode=total_mode,
            )
        logger.debug(
            "DiagnosticReports listed",
            extra={
                "event": "diagnostic_report.listed",
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
        tenant_id: str | None = None,
        status: DiagnosticReportStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[DiagnosticReportModel], int | None]:
        return await self.list(
            tenant_id=tenant_id, user_id=user_id, status=status,
            subject=subject, identifier=identifier, limit=limit, offset=offset,
            sort=sort, total_mode=total_mode,
        )

    async def delete(self, diagnostic_report_id: int) -> bool:
        """Every sub-resource here is a plain two/three-level
        child/grandchild, so a plain ORM `session.delete()` with every
        relationship's own `cascade="all, delete-orphan"` is safe and
        sufficient."""
        async with self.session_factory() as session:
            stmt = select(DiagnosticReportModel).where(
                DiagnosticReportModel.diagnostic_report_id == diagnostic_report_id
            )
            dr = (await session.execute(stmt)).scalars().first()
            if not dr:
                return False
            try:
                await session.delete(dr)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
