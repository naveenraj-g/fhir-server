from sqlalchemy import select

from app.core.logging import get_logger
from app.models.practitioner_role import PractitionerRoleModel

from ._indexer import INDEX_RELATIONSHIPS, index_columns, index_rows, local_references
from ._shared import REFERENCE_PARSERS, _validate_reference, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


async def _validate_local_references(session, tenant_id: str, document: dict) -> None:
    """Existence-check every relative local reference in the document —
    practitioner, organization, identifier.assigner, location[],
    healthcareService[] and endpoint[] — scoped to the caller's org; 422 if
    one doesn't resolve."""
    for label, resource_type, ref in local_references(document):
        ref_type, ref_id = REFERENCE_PARSERS[resource_type](ref)
        await _validate_reference(session, tenant_id, ref_type, ref_id, label)


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR PractitionerRole
    document: it's stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> PractitionerRoleModel:
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            practitioner_role = PractitionerRoleModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(practitioner_role)
            try:
                await session.commit()
                await session.refresh(practitioner_role)
            except Exception:
                await session.rollback()
                raise
            return practitioner_role

    async def patch_full(
        self,
        practitioner_role_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> PractitionerRoleModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerRoleModel).where(
                    PractitionerRoleModel.practitioner_role_id == practitioner_role_id
                )
            )
            practitioner_role = (await session.execute(stmt)).scalars().first()
            if not practitioner_role:
                return None

            await _validate_local_references(session, practitioner_role.tenant_id, document)

            practitioner_role.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(practitioner_role, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(practitioner_role, rel, rows[rel])
            if updated_by is not None:
                practitioner_role.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(practitioner_role)
            except Exception:
                await session.rollback()
                raise
            return practitioner_role
