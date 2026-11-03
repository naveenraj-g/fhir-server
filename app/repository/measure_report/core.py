from sqlalchemy import cast, delete, func, String
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.measure_report import (
    MeasureReportIdentifier,
    MeasureReportModel,
    MeasureReportStatus,
    MeasureReportType,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for MeasureReport."""

    async def get_by_measure_report_id(self, measure_report_id: int) -> MeasureReportModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MeasureReportModel).where(
                    MeasureReportModel.measure_report_id == measure_report_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_measure_report_id_in_org(
        self, measure_report_id: int, org_id: str
    ) -> MeasureReportModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MeasureReportModel).where(
                    MeasureReportModel.measure_report_id == measure_report_id,
                    MeasureReportModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def measure_report_belongs_to_org(self, measure_report_id: int, org_id: str) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(MeasureReportModel.id)).where(
                MeasureReportModel.measure_report_id == measure_report_id,
                MeasureReportModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        identifier: str | None = None,
        status: str | None = None,
        type: str | None = None,
        measure: str | None = None,
        subject: str | None = None,
        reporter: str | None = None,
        date: str | None = None,
    ):
        stmt = stmt.where(MeasureReportModel.tenant_id == org_id)

        if identifier:
            conditions = [MeasureReportIdentifier.measure_report_pk == MeasureReportModel.id]
            if "|" in identifier:
                sys, val = identifier.split("|", 1)
                if sys:
                    conditions.append(MeasureReportIdentifier.system == sys)
                if val:
                    conditions.append(MeasureReportIdentifier.value == val)
            else:
                conditions.append(MeasureReportIdentifier.value == identifier)
            stmt = apply_child_exists_filter(
                stmt,
                select(MeasureReportIdentifier.id).where(*conditions),
            )

        if status:
            val = status.value if hasattr(status, "value") else str(status)
            stmt = stmt.where(MeasureReportModel.status == MeasureReportStatus(val))

        if type:
            val = type.value if hasattr(type, "value") else str(type)
            stmt = stmt.where(MeasureReportModel.type == MeasureReportType(val))

        if measure:
            stmt = stmt.where(MeasureReportModel.measure == measure)

        if subject:
            stmt = stmt.where(MeasureReportModel.subject_reference == subject)

        if reporter:
            stmt = stmt.where(MeasureReportModel.reporter_reference == reporter)

        if date:
            stmt = stmt.where(cast(MeasureReportModel.date, String).startswith(date))

        return stmt

    async def list(
        self,
        *,
        org_id: str,
        identifier: str | None = None,
        status: str | None = None,
        type: str | None = None,
        measure: str | None = None,
        subject: str | None = None,
        reporter: str | None = None,
        date: str | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MeasureReportModel], int]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(MeasureReportModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                identifier=identifier,
                status=status,
                type=type,
                measure=measure,
                subject=subject,
                reporter=reporter,
                date=date,
            )
            total = (await session.execute(count_stmt)).scalar() or 0

            data_stmt = select(MeasureReportModel)
            data_stmt = self._apply_list_filters(
                data_stmt,
                org_id=org_id,
                identifier=identifier,
                status=status,
                type=type,
                measure=measure,
                subject=subject,
                reporter=reporter,
                date=date,
            )
            data_stmt = _with_relationships(data_stmt)

            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                MeasureReportModel.measure_report_id,
                default_desc=True,
            )
            order_by = sort_column.desc() if sort_desc else sort_column.asc()
            data_stmt = data_stmt.order_by(order_by).limit(limit).offset(offset)

            items = (await session.execute(data_stmt)).scalars().all()
            return list(items), total

    async def delete(self, measure_report_id: int, org_id: str | None = None) -> bool:
        async with self.session_factory() as session:
            stmt = delete(MeasureReportModel).where(
                MeasureReportModel.measure_report_id == measure_report_id
            )
            if org_id:
                stmt = stmt.where(MeasureReportModel.tenant_id == org_id)
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0
