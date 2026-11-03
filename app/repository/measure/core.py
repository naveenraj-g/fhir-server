from sqlalchemy import delete, func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.measure import (
    MeasureIdentifier,
    MeasureModel,
    MeasureStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for Measure."""

    async def get_by_measure_id(self, measure_id: int) -> MeasureModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MeasureModel).where(MeasureModel.measure_id == measure_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_measure_id_in_org(
        self, measure_id: int, org_id: str
    ) -> MeasureModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MeasureModel).where(
                    MeasureModel.measure_id == measure_id,
                    MeasureModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def measure_belongs_to_org(self, measure_id: int, org_id: str) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(MeasureModel.id)).where(
                MeasureModel.measure_id == measure_id,
                MeasureModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str,
        url: str | None = None,
        identifier: str | None = None,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        publisher: str | None = None,
        description: str | None = None,
    ):
        stmt = stmt.where(MeasureModel.tenant_id == org_id)

        if url:
            stmt = stmt.where(MeasureModel.url == url)

        if identifier:
            conditions = [MeasureIdentifier.measure_pk == MeasureModel.id]
            if "|" in identifier:
                sys, val = identifier.split("|", 1)
                if sys:
                    conditions.append(MeasureIdentifier.system == sys)
                if val:
                    conditions.append(MeasureIdentifier.value == val)
            else:
                conditions.append(MeasureIdentifier.value == identifier)
            stmt = apply_child_exists_filter(
                stmt,
                select(MeasureIdentifier.id).where(*conditions),
            )

        if name:
            stmt = stmt.where(MeasureModel.name.ilike(f"%{name}%"))

        if title:
            stmt = stmt.where(MeasureModel.title.ilike(f"%{title}%"))

        if status:
            val = status.value if hasattr(status, "value") else str(status)
            stmt = stmt.where(MeasureModel.status == MeasureStatus(val))

        if publisher:
            stmt = stmt.where(MeasureModel.publisher.ilike(f"%{publisher}%"))

        if description:
            stmt = stmt.where(MeasureModel.description.ilike(f"%{description}%"))

        return stmt

    async def list(
        self,
        *,
        org_id: str,
        url: str | None = None,
        identifier: str | None = None,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        publisher: str | None = None,
        description: str | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MeasureModel], int]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(MeasureModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                url=url,
                identifier=identifier,
                name=name,
                title=title,
                status=status,
                publisher=publisher,
                description=description,
            )
            total = (await session.execute(count_stmt)).scalar() or 0

            data_stmt = select(MeasureModel)
            data_stmt = self._apply_list_filters(
                data_stmt,
                org_id=org_id,
                url=url,
                identifier=identifier,
                name=name,
                title=title,
                status=status,
                publisher=publisher,
                description=description,
            )
            data_stmt = _with_relationships(data_stmt)

            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                MeasureModel.measure_id,
                default_desc=True,
            )
            order_by = sort_column.desc() if sort_desc else sort_column.asc()
            data_stmt = data_stmt.order_by(order_by).limit(limit).offset(offset)

            items = (await session.execute(data_stmt)).scalars().all()
            return list(items), total

    async def delete(self, measure_id: int, org_id: str | None = None) -> bool:
        async with self.session_factory() as session:
            stmt = delete(MeasureModel).where(MeasureModel.measure_id == measure_id)
            if org_id:
                stmt = stmt.where(MeasureModel.tenant_id == org_id)
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0
