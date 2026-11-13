from sqlalchemy import select

from app.core.logging import get_logger
from app.errors.domain import BusinessRuleViolationError
from app.models.location import LocationModel

from ._indexer import (
    INDEX_RELATIONSHIPS,
    assigner_references,
    index_columns,
    index_rows,
    managing_organization_reference,
    part_of_reference,
)
from ._shared import (
    _parse_location_ref,
    _parse_org_ref,
    _partof_chain_contains,
    _validate_reference,
    _with_relationships,
)

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


async def _validate_local_references(session, tenant_id: str, document: dict) -> int | None:
    """Existence-check every relative local Reference in the document —
    managingOrganization, partOf and identifier.assigner — scoped to the
    caller's org (422 if one doesn't resolve). Returns partOf's resolved
    public id, if any. Absolute URLs aren't checked: they point elsewhere."""
    org_ref = managing_organization_reference(document)
    if org_ref:
        ref_type, ref_id = _parse_org_ref(org_ref)
        await _validate_reference(session, tenant_id, ref_type, ref_id, "managingOrganization")
    part_of_id = None
    part_of = part_of_reference(document)
    if part_of:
        ref_type, part_of_id = _parse_location_ref(part_of)
        await _validate_reference(session, tenant_id, ref_type, part_of_id, "partOf")
    for ref in assigner_references(document):
        ref_type, ref_id = _parse_org_ref(ref)
        await _validate_reference(session, tenant_id, ref_type, ref_id, "identifier.assigner")
    return part_of_id


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR Location
    document: it's stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py) — same arrangement as Organization."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> LocationModel:
        """No partOf cycle check is needed here (unlike patch_full): the row
        doesn't exist yet, so it can't already be an ancestor of the
        location it's being attached to."""
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            loc = LocationModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(loc)
            try:
                await session.commit()
                await session.refresh(loc)
            except Exception:
                await session.rollback()
                raise
            return loc

    async def patch_full(
        self,
        location_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> LocationModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt. Rejects a partOf that would make the hierarchy circular."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(LocationModel).where(LocationModel.location_id == location_id)
            )
            loc = (await session.execute(stmt)).scalars().first()
            if not loc:
                return None

            part_of_id = await _validate_local_references(session, loc.tenant_id, document)
            if part_of_id is not None and await _partof_chain_contains(
                session, loc.tenant_id, part_of_id, loc.location_id
            ):
                raise BusinessRuleViolationError(
                    f"Setting partOf to Location/{part_of_id} would create a "
                    "circular location hierarchy."
                )

            loc.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(loc, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(loc, rel, rows[rel])
            if updated_by is not None:
                loc.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(loc)
            except Exception:
                await session.rollback()
                raise
            return loc
