from sqlalchemy import exists, func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.enums import OrganizationReferenceType
from app.models.organization.enums import OrganizationEndpointReferenceType
from app.models.organization import (
    OrganizationAddress,
    OrganizationAlias,
    OrganizationEndpoint,
    OrganizationIdentifier,
    OrganizationModel,
    OrganizationType,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the Organization parent row (no sub-resources)."""

    async def get_by_organization_id(
        self, organization_id: int
    ) -> OrganizationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(OrganizationModel).where(
                    OrganizationModel.organization_id == organization_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_organization_id_in_org(
        self, organization_id: int, org_id: str
    ) -> OrganizationModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the organization exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(OrganizationModel).where(
                    OrganizationModel.organization_id == organization_id,
                    OrganizationModel.org_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def organization_belongs_to_org(
        self, organization_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the organization exists AND belongs
        to org_id."""
        async with self.session_factory() as session:
            stmt = select(OrganizationModel.id).where(
                OrganizationModel.organization_id == organization_id,
                OrganizationModel.org_id == org_id,
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
        org_type: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        partof: str | None = None,
        endpoint: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(OrganizationModel.org_id == org_id)
        stmt = apply_token_filter(stmt, OrganizationModel.active, active)
        if name:
            # Medplum: "name" matches the organization's name OR any alias —
            # unlike Patient/Practitioner's "name" (HumanName sub-fields),
            # Organization has no HumanName; this is the resource's own quirk.
            pattern = f"%{name}%"
            stmt = stmt.where(
                or_(
                    OrganizationModel.name.ilike(pattern),
                    exists(
                        select(OrganizationAlias.id).where(
                            OrganizationAlias.organization_id == OrganizationModel.id,
                            OrganizationAlias.value.ilike(pattern),
                        )
                    ),
                )
            )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationIdentifier.id).where(
                    OrganizationIdentifier.organization_id == OrganizationModel.id,
                    OrganizationIdentifier.value == identifier,
                ),
            )
        if org_type:
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationType.id).where(
                    OrganizationType.organization_id == OrganizationModel.id,
                    OrganizationType.coding_code == org_type,
                ),
            )
        if address:
            pattern = f"%{address}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationAddress.id).where(
                    OrganizationAddress.organization_id == OrganizationModel.id,
                    or_(
                        OrganizationAddress.line.ilike(pattern),
                        OrganizationAddress.city.ilike(pattern),
                        OrganizationAddress.district.ilike(pattern),
                        OrganizationAddress.state.ilike(pattern),
                        OrganizationAddress.country.ilike(pattern),
                        OrganizationAddress.postal_code.ilike(pattern),
                        OrganizationAddress.text.ilike(pattern),
                    ),
                ),
            )
        if address_city:
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationAddress.id).where(
                    OrganizationAddress.organization_id == OrganizationModel.id,
                    OrganizationAddress.city.ilike(f"%{address_city}%"),
                ),
            )
        if address_state:
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationAddress.id).where(
                    OrganizationAddress.organization_id == OrganizationModel.id,
                    OrganizationAddress.state.ilike(f"%{address_state}%"),
                ),
            )
        if address_postal_code:
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationAddress.id).where(
                    OrganizationAddress.organization_id == OrganizationModel.id,
                    OrganizationAddress.postal_code == address_postal_code,
                ),
            )
        if address_country:
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationAddress.id).where(
                    OrganizationAddress.organization_id == OrganizationModel.id,
                    OrganizationAddress.country.ilike(f"%{address_country}%"),
                ),
            )
        if address_use is not None:
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationAddress.id).where(
                    OrganizationAddress.organization_id == OrganizationModel.id,
                    OrganizationAddress.use == address_use,
                ),
            )
        if partof:
            _, partof_ref_id = parse_reference(partof, OrganizationReferenceType)
            stmt = apply_token_filter(stmt, OrganizationModel.partof_id, partof_ref_id)
        if endpoint:
            ep_type, ep_id = parse_reference(
                endpoint, OrganizationEndpointReferenceType
            )
            stmt = apply_child_exists_filter(
                stmt,
                select(OrganizationEndpoint.id).where(
                    OrganizationEndpoint.organization_id == OrganizationModel.id,
                    OrganizationEndpoint.reference_type == ep_type,
                    OrganizationEndpoint.reference_id == ep_id,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        name: str | None = None,
        identifier: str | None = None,
        org_type: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        partof: str | None = None,
        endpoint: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[OrganizationModel], int | None]:
        """Paginated, filtered, sorted list of organizations. Returns
        (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "active": active,
                "name": name,
                "identifier": identifier,
                "org_type": org_type,
                "address": address,
                "address_city": address_city,
                "address_state": address_state,
                "address_postal_code": address_postal_code,
                "address_country": address_country,
                "address_use": address_use,
                "partof": partof,
                "endpoint": endpoint,
            }
            base = self._apply_list_filters(
                _with_relationships(select(OrganizationModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(OrganizationModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=OrganizationModel.organization_id,
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
            "Organizations listed",
            extra={
                "event": "organization.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(
                    k for k, v in filter_kwargs.items() if v is not None
                ),
            },
        )
        return rows, total

    # ── Delete ────────────────────────────────────────────────────────────────
    # create()/patch() live in full.py — Organization has no separate
    # scalar-only variant, see OrganizationCreateSchema's docstring.

    async def delete(self, organization_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(OrganizationModel).where(
                OrganizationModel.organization_id == organization_id
            )
            org = (await session.execute(stmt)).scalars().first()
            if not org:
                return False
            try:
                await session.delete(org)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
