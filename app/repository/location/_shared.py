from sqlalchemy import exists, literal, select
from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.location import LocationModel
from app.models.location.enums import (
    LocationEndpointReferenceType,
    LocationPartOfReferenceType,
)
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_SORTABLE_FIELDS",
    "_location_ref_kwargs",
    "_org_ref_kwargs",
    "_parse_endpoint_ref",
    "_parse_location_ref",
    "_parse_org_ref",
    "_partof_chain_contains",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors Organization's _shared.py.
_SORTABLE_FIELDS = {
    "location_id": LocationModel.location_id,
    "name": LocationModel.name,
    "status": LocationModel.status,
    "created_at": LocationModel.created_at,
    "updated_at": LocationModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load all location sub-resources to avoid N+1 and async lazy-load
    failures. Location's sub-resources are all one level deep — there is no
    nested list like Organization.contact.telecom — so no chained
    selectinload is needed."""
    return stmt.options(
        selectinload(LocationModel.identifiers),
        selectinload(LocationModel.types),
        selectinload(LocationModel.aliases),
        selectinload(LocationModel.telecoms),
        selectinload(LocationModel.hours_of_operation),
        selectinload(LocationModel.endpoints),
    )


def _parse_location_ref(ref: str) -> tuple:
    """Parse 'Location/230001' → (LocationPartOfReferenceType.Location, 230001).
    Used for Location.partOf, the self-referential containment link."""
    return parse_reference(ref, LocationPartOfReferenceType)


def _location_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a Reference(Location) string. The Location counterpart of
    app.repository._reference_shared._org_ref_kwargs, which is bound to
    OrganizationReferenceType."""
    ref_type, ref_id = _parse_location_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_endpoint_ref(ref: str) -> tuple:
    """Parse 'Endpoint/1' → (LocationEndpointReferenceType.Endpoint, 1).
    Endpoint isn't a modeled resource in this system (no RESOURCE_REGISTRY
    entry, see app/core/reference_resolver.py) so — unlike every
    Reference(Organization)/Reference(Location) field — there's no existence
    check to run here; the identifier fallback (see LocationEndpointInput) is
    often the only populated half."""
    return parse_reference(ref, LocationEndpointReferenceType)


async def _partof_chain_contains(
    session,
    org_id: str,
    start_public_id: int | None,
    target_public_id: int,
    max_depth: int = 100,
) -> bool:
    """Walks the partOf ancestor chain starting at start_public_id
    (location_id, the PUBLIC sequence id — same convention as every other
    flattened Reference field, see app/core/filters.py's docstring). Returns
    True if target_public_id appears in that chain (including immediately,
    i.e. start==target — catches direct self-reference).

    Location.partOf is self-referential ("Another Location of which this
    Location is physically a part of"), so without this a client could build
    a cycle — A inside B inside A — which would make any hierarchy walk
    (breadcrumbs, "all rooms in this building") loop forever.

    Scoped to org_id at every step — this application is tenant-scoped end to
    end, so the walk never crosses into another tenant's rows even as a
    defensive measure (on top of _validate_reference already confirming partOf
    resolves within the same org_id at write time).

    Implemented as a single recursive CTE (one DB round trip) rather than a
    per-level Python loop with one query per level. max_depth still bounds the
    recursion (Postgres doesn't auto-detect cycles in WITH RECURSIVE) against
    any pre-existing corrupt/looping data.
    """
    if start_public_id is None:
        return False

    anchor = select(
        LocationModel.location_id.label("location_id"),
        LocationModel.part_of_id.label("part_of_id"),
        literal(1).label("depth"),
    ).where(
        LocationModel.location_id == start_public_id,
        LocationModel.org_id == org_id,
    )
    chain = anchor.cte(name="part_of_ancestor_chain", recursive=True)

    step = (
        select(
            LocationModel.location_id.label("location_id"),
            LocationModel.part_of_id.label("part_of_id"),
            (chain.c.depth + 1).label("depth"),
        )
        .join(chain, LocationModel.location_id == chain.c.part_of_id)
        .where(
            LocationModel.org_id == org_id,
            chain.c.depth < max_depth,
        )
    )
    chain = chain.union_all(step)

    stmt = select(
        exists(
            select(1).select_from(chain).where(chain.c.location_id == target_public_id)
        )
    )
    result = await session.execute(stmt)
    return bool(result.scalar())
