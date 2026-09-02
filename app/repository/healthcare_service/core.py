from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.enums import OrganizationReferenceType
from app.models.healthcare_service import (
    HealthcareServiceCategory,
    HealthcareServiceCharacteristic,
    HealthcareServiceCoverageArea,
    HealthcareServiceEndpoint,
    HealthcareServiceIdentifier,
    HealthcareServiceLocation,
    HealthcareServiceModel,
    HealthcareServiceProgram,
    HealthcareServiceSpecialty,
    HealthcareServiceType,
)
from app.models.healthcare_service.enums import (
    HealthcareServiceCoverageAreaReferenceType,
    HealthcareServiceEndpointReferenceType,
    HealthcareServiceLocationReferenceType,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the HealthcareService parent row (no sub-resources)."""

    async def get_by_healthcare_service_id(
        self, healthcare_service_id: int
    ) -> HealthcareServiceModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(HealthcareServiceModel).where(
                    HealthcareServiceModel.healthcare_service_id
                    == healthcare_service_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_healthcare_service_id_in_org(
        self, healthcare_service_id: int, org_id: str
    ) -> HealthcareServiceModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the healthcare service exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(HealthcareServiceModel).where(
                    HealthcareServiceModel.healthcare_service_id
                    == healthcare_service_id,
                    HealthcareServiceModel.org_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def healthcare_service_belongs_to_org(
        self, healthcare_service_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the healthcare service exists AND
        belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(HealthcareServiceModel.id).where(
                HealthcareServiceModel.healthcare_service_id == healthcare_service_id,
                HealthcareServiceModel.org_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        active: bool | None = None,
        name: str | None = None,
        identifier: str | None = None,
        category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        characteristic: str | None = None,
        program: str | None = None,
        provided_by: str | None = None,
        location: str | None = None,
        coverage_area: str | None = None,
        endpoint: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(HealthcareServiceModel.org_id == org_id)
        stmt = apply_token_filter(stmt, HealthcareServiceModel.active, active)
        if name:
            stmt = stmt.where(HealthcareServiceModel.name.ilike(f"%{name}%"))
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceIdentifier.id).where(
                    HealthcareServiceIdentifier.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceIdentifier.value == identifier,
                ),
            )
        if category:
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceCategory.id).where(
                    HealthcareServiceCategory.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceCategory.coding_code == category,
                ),
            )
        if service_type:
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceType.id).where(
                    HealthcareServiceType.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceType.coding_code == service_type,
                ),
            )
        if specialty:
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceSpecialty.id).where(
                    HealthcareServiceSpecialty.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceSpecialty.coding_code == specialty,
                ),
            )
        if characteristic:
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceCharacteristic.id).where(
                    HealthcareServiceCharacteristic.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceCharacteristic.coding_code == characteristic,
                ),
            )
        if program:
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceProgram.id).where(
                    HealthcareServiceProgram.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceProgram.coding_code == program,
                ),
            )
        if provided_by:
            _, pb_id = parse_reference(provided_by, OrganizationReferenceType)
            stmt = apply_token_filter(
                stmt, HealthcareServiceModel.provided_by_id, pb_id
            )
        if location:
            loc_type, loc_id = parse_reference(
                location, HealthcareServiceLocationReferenceType
            )
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceLocation.id).where(
                    HealthcareServiceLocation.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceLocation.reference_type == loc_type,
                    HealthcareServiceLocation.reference_id == loc_id,
                ),
            )
        if coverage_area:
            ca_type, ca_id = parse_reference(
                coverage_area, HealthcareServiceCoverageAreaReferenceType
            )
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceCoverageArea.id).where(
                    HealthcareServiceCoverageArea.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceCoverageArea.reference_type == ca_type,
                    HealthcareServiceCoverageArea.reference_id == ca_id,
                ),
            )
        if endpoint:
            ep_type, ep_id = parse_reference(
                endpoint, HealthcareServiceEndpointReferenceType
            )
            stmt = apply_child_exists_filter(
                stmt,
                select(HealthcareServiceEndpoint.id).where(
                    HealthcareServiceEndpoint.healthcare_service_id
                    == HealthcareServiceModel.id,
                    HealthcareServiceEndpoint.reference_type == ep_type,
                    HealthcareServiceEndpoint.reference_id == ep_id,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        name: str | None = None,
        identifier: str | None = None,
        category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        characteristic: str | None = None,
        program: str | None = None,
        provided_by: str | None = None,
        location: str | None = None,
        coverage_area: str | None = None,
        endpoint: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[HealthcareServiceModel], int | None]:
        """Paginated, filtered, sorted list of healthcare services. Returns
        (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "active": active,
                "name": name,
                "identifier": identifier,
                "category": category,
                "service_type": service_type,
                "specialty": specialty,
                "characteristic": characteristic,
                "program": program,
                "provided_by": provided_by,
                "location": location,
                "coverage_area": coverage_area,
                "endpoint": endpoint,
            }
            base = self._apply_list_filters(
                _with_relationships(select(HealthcareServiceModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(HealthcareServiceModel),
                **filter_kwargs,
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=HealthcareServiceModel.healthcare_service_id,
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
        logger.debug(
            "HealthcareServices listed",
            extra={
                "event": "healthcare_service.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    # ── Delete ────────────────────────────────────────────────────────────────
    # create()/patch() live in full.py — HealthcareService has no separate
    # scalar-only variant, see HealthcareServiceCreateSchema's docstring.

    async def delete(self, healthcare_service_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(HealthcareServiceModel).where(
                HealthcareServiceModel.healthcare_service_id == healthcare_service_id
            )
            hs = (await session.execute(stmt)).scalars().first()
            if not hs:
                return False
            try:
                await session.delete(hs)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
