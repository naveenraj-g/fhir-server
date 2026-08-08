import math

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.errors.domain import BusinessRuleViolationError
from app.models.enums import OrganizationReferenceType
from app.models.location import (
    LocationAlias,
    LocationEndpoint,
    LocationIdentifier,
    LocationModel,
    LocationType,
)
from app.models.location.enums import (
    LocationEndpointReferenceType,
    LocationPartOfReferenceType,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)

# FHIR `near` distance units. The R4 spec allows UCUM codes; Medplum documents
# km and mi. Anything else is rejected rather than silently treated as km.
_NEAR_UNITS_IN_KM = {
    "km": 1.0,
    "m": 0.001,
    "mi": 1.609344,
    "[mi_i]": 1.609344,
    "[mi_us]": 1.609344,
}

_EARTH_RADIUS_KM = 6371.0088


def _parse_near(near: str) -> tuple[float, float, float]:
    """Parse the FHIR `near` special search parameter.

    Format is `[latitude]|[longitude]|[distance]|[units]` (units optional,
    defaulting to km) — e.g. `near=42.25475478|-83.6945691|11.20|km`.
    https://www.hl7.org/fhir/R4/location.html#positional
    """
    parts = near.split("|")
    if len(parts) < 3:
        raise BusinessRuleViolationError(
            "near: expected '[latitude]|[longitude]|[distance]' with an optional "
            "'|[units]' suffix, e.g. '42.25475478|-83.6945691|11.20|km'"
        )
    try:
        lat = float(parts[0])
        lon = float(parts[1])
        distance = float(parts[2])
    except ValueError as exc:
        raise BusinessRuleViolationError(
            "near: latitude, longitude and distance must all be numbers"
        ) from exc

    units = (parts[3].strip() or "km") if len(parts) > 3 else "km"
    if units not in _NEAR_UNITS_IN_KM:
        raise BusinessRuleViolationError(
            f"near: unsupported distance unit '{units}' — "
            f"expected one of {', '.join(sorted(_NEAR_UNITS_IN_KM))}"
        )
    if not -90.0 <= lat <= 90.0 or not -180.0 <= lon <= 180.0:
        raise BusinessRuleViolationError(
            "near: latitude must be within [-90, 90] and longitude within [-180, 180]"
        )
    if distance < 0:
        raise BusinessRuleViolationError("near: distance must not be negative")

    return lat, lon, distance * _NEAR_UNITS_IN_KM[units]


class _CoreMixin:
    """Core CRUD for the Location parent row (no sub-resources)."""

    async def get_by_location_id(self, location_id: int) -> LocationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(LocationModel).where(LocationModel.location_id == location_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_location_id_in_org(
        self, location_id: int, org_id: str
    ) -> LocationModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the location exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(LocationModel).where(
                    LocationModel.location_id == location_id,
                    LocationModel.org_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def location_belongs_to_org(self, location_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the location exists AND belongs to
        org_id."""
        async with self.session_factory() as session:
            stmt = select(LocationModel.id).where(
                LocationModel.location_id == location_id,
                LocationModel.org_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        name: str | None = None,
        identifier: str | None = None,
        location_status=None,
        operational_status: str | None = None,
        location_type: str | None = None,
        physical_type: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        organization: str | None = None,
        partof: str | None = None,
        endpoint: str | None = None,
        near: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(LocationModel.org_id == org_id)

        if name:
            # Medplum: "name" matches Location.name OR Location.alias — the
            # same name-or-alias union Organization uses.
            pattern = f"%{name}%"
            stmt = stmt.where(
                or_(
                    LocationModel.name.ilike(pattern),
                    LocationModel.id.in_(
                        select(LocationAlias.location_id).where(
                            LocationAlias.value.ilike(pattern)
                        )
                    ),
                )
            )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(LocationIdentifier.id).where(
                    LocationIdentifier.location_id == LocationModel.id,
                    LocationIdentifier.value == identifier,
                ),
            )

        stmt = apply_token_filter(stmt, LocationModel.status, location_status)
        stmt = apply_token_filter(
            stmt, LocationModel.operational_status_code, operational_status
        )
        stmt = apply_token_filter(
            stmt, LocationModel.physical_type_code, physical_type
        )

        if location_type:
            stmt = apply_child_exists_filter(
                stmt,
                select(LocationType.id).where(
                    LocationType.location_id == LocationModel.id,
                    LocationType.coding_code == location_type,
                ),
            )

        # Location.address is 0..1 and flattened onto the parent row, so these
        # are plain WHERE clauses — no EXISTS subquery, unlike Organization's
        # 0..* address child table.
        if address:
            pattern = f"%{address}%"
            stmt = stmt.where(
                or_(
                    LocationModel.address_line.ilike(pattern),
                    LocationModel.address_city.ilike(pattern),
                    LocationModel.address_district.ilike(pattern),
                    LocationModel.address_state.ilike(pattern),
                    LocationModel.address_country.ilike(pattern),
                    LocationModel.address_postal_code.ilike(pattern),
                    LocationModel.address_text.ilike(pattern),
                )
            )
        if address_city:
            stmt = stmt.where(LocationModel.address_city.ilike(f"%{address_city}%"))
        if address_state:
            stmt = stmt.where(LocationModel.address_state.ilike(f"%{address_state}%"))
        if address_postal_code:
            stmt = stmt.where(
                LocationModel.address_postal_code == address_postal_code
            )
        if address_country:
            stmt = stmt.where(
                LocationModel.address_country.ilike(f"%{address_country}%")
            )
        stmt = apply_token_filter(stmt, LocationModel.address_use, address_use)

        if organization:
            _, org_ref_id = parse_reference(organization, OrganizationReferenceType)
            stmt = apply_token_filter(
                stmt, LocationModel.managing_organization_id, org_ref_id
            )

        if partof:
            _, partof_ref_id = parse_reference(partof, LocationPartOfReferenceType)
            stmt = apply_token_filter(stmt, LocationModel.part_of_id, partof_ref_id)

        if endpoint:
            ep_type, ep_id = parse_reference(endpoint, LocationEndpointReferenceType)
            stmt = apply_child_exists_filter(
                stmt,
                select(LocationEndpoint.id).where(
                    LocationEndpoint.location_id == LocationModel.id,
                    LocationEndpoint.reference_type == ep_type,
                    LocationEndpoint.reference_id == ep_id,
                ),
            )

        if near:
            lat, lon, radius_km = _parse_near(near)
            # Great-circle (haversine) distance computed in SQL against the
            # position_* columns. No PostGIS dependency, but also no spatial
            # index — this is a sequential scan over rows that have a
            # position, which is fine at this scale and swappable for
            # earthdistance/PostGIS later without changing the API surface.
            lat_rad = math.radians(lat)
            lon_rad = math.radians(lon)
            loc_lat = func.radians(LocationModel.position_latitude)
            loc_lon = func.radians(LocationModel.position_longitude)
            central_angle = func.acos(
                func.least(
                    1.0,
                    func.greatest(
                        -1.0,
                        func.sin(lat_rad) * func.sin(loc_lat)
                        + func.cos(lat_rad)
                        * func.cos(loc_lat)
                        * func.cos(loc_lon - lon_rad),
                    ),
                )
            )
            stmt = stmt.where(
                LocationModel.position_latitude.is_not(None),
                LocationModel.position_longitude.is_not(None),
                _EARTH_RADIUS_KM * central_angle <= radius_km,
            )

        return stmt

    async def list(
        self,
        org_id: str | None = None,
        name: str | None = None,
        identifier: str | None = None,
        location_status=None,
        operational_status: str | None = None,
        location_type: str | None = None,
        physical_type: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        organization: str | None = None,
        partof: str | None = None,
        endpoint: str | None = None,
        near: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[LocationModel], int | None]:
        """Paginated, filtered, sorted list of locations. Returns
        (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "name": name,
                "identifier": identifier,
                "location_status": location_status,
                "operational_status": operational_status,
                "location_type": location_type,
                "physical_type": physical_type,
                "address": address,
                "address_city": address_city,
                "address_state": address_state,
                "address_postal_code": address_postal_code,
                "address_country": address_country,
                "address_use": address_use,
                "organization": organization,
                "partof": partof,
                "endpoint": endpoint,
                "near": near,
            }
            base = self._apply_list_filters(
                _with_relationships(select(LocationModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(LocationModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=LocationModel.location_id,
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
            "Locations listed",
            extra={
                "event": "location.listed",
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
    # create()/patch() live in full.py — Location has no separate scalar-only
    # variant, see LocationCreateSchema's docstring.

    async def delete(self, location_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(LocationModel).where(
                LocationModel.location_id == location_id
            )
            loc = (await session.execute(stmt)).scalars().first()
            if not loc:
                return False
            try:
                await session.delete(loc)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
