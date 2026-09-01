from sqlalchemy import exists, literal, select
from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.organization import OrganizationContact, OrganizationModel
from app.models.organization.enums import OrganizationEndpointReferenceType
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
    "_org_ref_kwargs",
    "_parse_endpoint_ref",
    "_parse_org_ref",
    "_partof_chain_contains",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors Patient/Practitioner's
# _shared.py exactly.
_SORTABLE_FIELDS = {
    "organization_id": OrganizationModel.organization_id,
    "name": OrganizationModel.name,
    "created_at": OrganizationModel.created_at,
    "updated_at": OrganizationModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load all organization sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(OrganizationModel.identifiers),
        selectinload(OrganizationModel.types),
        selectinload(OrganizationModel.aliases),
        selectinload(OrganizationModel.telecoms),
        selectinload(OrganizationModel.addresses),
        selectinload(OrganizationModel.contacts).selectinload(
            OrganizationContact.telecoms
        ),
        selectinload(OrganizationModel.endpoints),
    )


def _parse_endpoint_ref(ref: str) -> tuple:
    """Parse 'Endpoint/1' → (OrganizationEndpointReferenceType.Endpoint, 1).
    Endpoint isn't a modeled resource in this system (no RESOURCE_REGISTRY
    entry, see app/core/reference_resolver.py) so — unlike every
    Reference(Organization) field — there's no existence check to run here;
    the identifier fallback (see OrganizationEndpointInput) is often the only
    populated half."""
    return parse_reference(ref, OrganizationEndpointReferenceType)


async def _partof_chain_contains(
    session,
    org_id: str,
    start_public_id: int | None,
    target_public_id: int,
    max_depth: int = 100,
) -> bool:
    """Walks the partOf ancestor chain starting at start_public_id
    (organization_id, the PUBLIC sequence id — same convention as every other
    flattened Reference field, see app/core/filters.py's docstring). Returns
    True if target_public_id appears in that chain (including immediately,
    i.e. start==target — catches direct self-reference).

    Scoped to org_id at every step — this application is tenant-scoped end
    to end, so the walk never crosses into another tenant's rows even as a
    defensive measure (on top of _validate_reference already confirming
    partOf resolves within the same org_id at write time).

    Implemented as a single recursive CTE (one DB round trip) rather than a
    per-level Python loop with one query per level. max_depth still bounds
    the recursion (Postgres doesn't auto-detect cycles in WITH RECURSIVE)
    against any pre-existing corrupt/looping data.
    """
    if start_public_id is None:
        return False

    anchor = select(
        OrganizationModel.organization_id.label("organization_id"),
        OrganizationModel.partof_id.label("partof_id"),
        literal(1).label("depth"),
    ).where(
        OrganizationModel.organization_id == start_public_id,
        OrganizationModel.org_id == org_id,
    )
    chain = anchor.cte(name="partof_ancestor_chain", recursive=True)

    step = (
        select(
            OrganizationModel.organization_id.label("organization_id"),
            OrganizationModel.partof_id.label("partof_id"),
            (chain.c.depth + 1).label("depth"),
        )
        .join(chain, OrganizationModel.organization_id == chain.c.partof_id)
        .where(
            OrganizationModel.org_id == org_id,
            chain.c.depth < max_depth,
        )
    )
    chain = chain.union_all(step)

    stmt = select(
        exists(
            select(1)
            .select_from(chain)
            .where(chain.c.organization_id == target_public_id)
        )
    )
    result = await session.execute(stmt)
    return bool(result.scalar())
