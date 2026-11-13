from sqlalchemy import select

from app.core.logging import get_logger
from app.errors.domain import BusinessRuleViolationError
from app.models.organization import OrganizationModel

from ._indexer import (
    INDEX_RELATIONSHIPS,
    assigner_references,
    index_columns,
    index_rows,
    partof_reference,
)
from ._shared import (
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


async def _validate_local_references(
    session, tenant_id: str, document: dict
) -> int | None:
    """Existence-check every relative Reference(Organization) in the
    document, scoped to the caller's org (422 if one doesn't resolve).
    Returns partOf's resolved public id, if any."""
    partof_id = None
    partof = partof_reference(document)
    if partof:
        ref_type, partof_id = _parse_org_ref(partof)
        await _validate_reference(session, tenant_id, ref_type, partof_id, "partOf")
    for ref in assigner_references(document):
        ref_type, ref_id = _parse_org_ref(ref)
        await _validate_reference(
            session, tenant_id, ref_type, ref_id, "identifier.assigner"
        )
    return partof_id


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR Organization
    document: it's stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> OrganizationModel:
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            org = OrganizationModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(org)
            try:
                await session.commit()
                await session.refresh(org)
            except Exception:
                await session.rollback()
                raise
            return org

    async def patch_full(
        self,
        organization_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> OrganizationModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(OrganizationModel).where(
                    OrganizationModel.organization_id == organization_id
                )
            )
            org = (await session.execute(stmt)).scalars().first()
            if not org:
                return None

            partof_id = await _validate_local_references(
                session, org.tenant_id, document
            )
            if partof_id is not None and await _partof_chain_contains(
                session, org.tenant_id, partof_id, org.organization_id
            ):
                raise BusinessRuleViolationError(
                    f"Setting partOf to Organization/{partof_id} would create a "
                    "circular organization hierarchy."
                )

            org.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(org, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(org, rel, rows[rel])
            if updated_by is not None:
                org.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(org)
            except Exception:
                await session.rollback()
                raise
            return org
