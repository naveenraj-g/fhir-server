from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.enums import OrganizationReferenceType, PractitionerReferenceType
from app.models.practitioner_role import (
    PractitionerRoleCode,
    PractitionerRoleCodeCoding,
    PractitionerRoleEndpoint,
    PractitionerRoleHealthcareService,
    PractitionerRoleIdentifier,
    PractitionerRoleLocation,
    PractitionerRoleModel,
    PractitionerRoleSpecialty,
    PractitionerRoleSpecialtyCoding,
)
from app.models.practitioner_role.enums import (
    PractitionerRoleEndpointReferenceType,
    PractitionerRoleHealthcareServiceReferenceType,
    PractitionerRoleLocationReferenceType,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the PractitionerRole parent row (no sub-resources)."""

    async def get_by_practitioner_role_id(
        self, practitioner_role_id: int
    ) -> PractitionerRoleModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerRoleModel).where(
                    PractitionerRoleModel.practitioner_role_id == practitioner_role_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_practitioner_role_id_in_org(
        self, practitioner_role_id: int, org_id: str
    ) -> PractitionerRoleModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the practitioner role exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerRoleModel).where(
                    PractitionerRoleModel.practitioner_role_id == practitioner_role_id,
                    PractitionerRoleModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def practitioner_role_belongs_to_org(
        self, practitioner_role_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the practitioner role exists AND
        belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(PractitionerRoleModel.id).where(
                PractitionerRoleModel.practitioner_role_id == practitioner_role_id,
                PractitionerRoleModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        active: bool | None = None,
        identifier: str | None = None,
        code: str | None = None,
        specialty: str | None = None,
        practitioner: str | None = None,
        organization: str | None = None,
        location: str | None = None,
        healthcare_service: str | None = None,
        endpoint: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(PractitionerRoleModel.tenant_id == org_id)
        stmt = apply_token_filter(stmt, PractitionerRoleModel.active, active)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerRoleIdentifier.id).where(
                    PractitionerRoleIdentifier.practitioner_role_pk
                    == PractitionerRoleModel.id,
                    PractitionerRoleIdentifier.value == identifier,
                ),
            )
        # code/specialty: each CodeableConcept's coding is a real 0..* child
        # table now — one EXISTS joining the coding table to its parent row,
        # correlated to the outer PractitionerRoleModel. Mirrors
        # HealthcareService's own category filter.
        if code:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerRoleCodeCoding.id)
                .join(
                    PractitionerRoleCode,
                    PractitionerRoleCodeCoding.practitioner_role_code_id
                    == PractitionerRoleCode.id,
                )
                .where(
                    PractitionerRoleCode.practitioner_role_pk
                    == PractitionerRoleModel.id,
                    PractitionerRoleCodeCoding.code == code,
                ),
            )
        if specialty:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerRoleSpecialtyCoding.id)
                .join(
                    PractitionerRoleSpecialty,
                    PractitionerRoleSpecialtyCoding.practitioner_role_specialty_id
                    == PractitionerRoleSpecialty.id,
                )
                .where(
                    PractitionerRoleSpecialty.practitioner_role_pk
                    == PractitionerRoleModel.id,
                    PractitionerRoleSpecialtyCoding.code == specialty,
                ),
            )
        if practitioner:
            _, p_id = parse_reference(practitioner, PractitionerReferenceType)
            stmt = apply_token_filter(
                stmt, PractitionerRoleModel.practitioner_id, p_id
            )
        if organization:
            _, org_ref_id = parse_reference(organization, OrganizationReferenceType)
            stmt = apply_token_filter(
                stmt, PractitionerRoleModel.organization_id, org_ref_id
            )
        if location:
            loc_type, loc_id = parse_reference(
                location, PractitionerRoleLocationReferenceType
            )
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerRoleLocation.id).where(
                    PractitionerRoleLocation.practitioner_role_pk
                    == PractitionerRoleModel.id,
                    PractitionerRoleLocation.reference_type == loc_type,
                    PractitionerRoleLocation.reference_id == loc_id,
                ),
            )
        if healthcare_service:
            hs_type, hs_id = parse_reference(
                healthcare_service, PractitionerRoleHealthcareServiceReferenceType
            )
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerRoleHealthcareService.id).where(
                    PractitionerRoleHealthcareService.practitioner_role_pk
                    == PractitionerRoleModel.id,
                    PractitionerRoleHealthcareService.reference_type == hs_type,
                    PractitionerRoleHealthcareService.reference_id == hs_id,
                ),
            )
        if endpoint:
            ep_type, ep_id = parse_reference(
                endpoint, PractitionerRoleEndpointReferenceType
            )
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerRoleEndpoint.id).where(
                    PractitionerRoleEndpoint.practitioner_role_pk
                    == PractitionerRoleModel.id,
                    PractitionerRoleEndpoint.reference_type == ep_type,
                    PractitionerRoleEndpoint.reference_id == ep_id,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        identifier: str | None = None,
        code: str | None = None,
        specialty: str | None = None,
        practitioner: str | None = None,
        organization: str | None = None,
        location: str | None = None,
        healthcare_service: str | None = None,
        endpoint: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PractitionerRoleModel], int | None]:
        """Paginated, filtered, sorted list of practitioner roles. Returns
        (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "active": active,
                "identifier": identifier,
                "code": code,
                "specialty": specialty,
                "practitioner": practitioner,
                "organization": organization,
                "location": location,
                "healthcare_service": healthcare_service,
                "endpoint": endpoint,
            }
            base = self._apply_list_filters(
                _with_relationships(select(PractitionerRoleModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PractitionerRoleModel),
                **filter_kwargs,
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=PractitionerRoleModel.practitioner_role_id,
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
            "PractitionerRoles listed",
            extra={
                "event": "practitioner_role.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    # ── Delete ────────────────────────────────────────────────────────────────
    # create()/patch() live in full.py — PractitionerRole has no separate
    # scalar-only variant, see PractitionerRoleCreateSchema's docstring.

    async def delete(self, practitioner_role_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(PractitionerRoleModel).where(
                PractitionerRoleModel.practitioner_role_id == practitioner_role_id
            )
            pr = (await session.execute(stmt)).scalars().first()
            if not pr:
                return False
            try:
                await session.delete(pr)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
