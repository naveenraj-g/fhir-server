from sqlalchemy import exists, literal, select
from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.location import LocationModel
from app.models.location.enums import (
    LocationEndpointReferenceType,
    LocationPartOfReferenceType,
)
from app.repository._reference_shared import _parse_org_ref, _validate_reference

__all__ = [
    "_parse_endpoint_ref",
    "_parse_location_ref",
    "_parse_org_ref",
    "_partof_chain_contains",
    "_validate_reference",
    "_with_relationships",
]


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from LocationModel.content."""
    return stmt.options(
        *(
            selectinload(getattr(LocationModel, rel))
            for rel in ("identifiers", "types", "endpoints")
        )
    )


def _parse_location_ref(ref: str) -> tuple:
    """Parse 'Location/230001' → (LocationPartOfReferenceType.Location, 230001).
    Used for Location.partOf, the self-referential containment link."""
    return parse_reference(ref, LocationPartOfReferenceType)


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
        LocationModel.tenant_id == org_id,
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
            LocationModel.tenant_id == org_id,
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
