from sqlalchemy import select

from app.core.logging import get_logger
from app.models.practitioner import PractitionerModel

from ._indexer import (
    INDEX_RELATIONSHIPS,
    index_columns,
    index_rows,
    organization_references,
    user_id_of,
)
from ._shared import _parse_org_ref, _validate_reference, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


async def _validate_local_references(session, tenant_id: str, document: dict) -> None:
    """Existence-check every relative Reference(Organization) in the
    document (identifier.assigner, qualification.issuer), scoped to the
    caller's org — 422 if one doesn't resolve."""
    for label, ref in organization_references(document):
        ref_type, ref_id = _parse_org_ref(ref)
        await _validate_reference(session, tenant_id, ref_type, ref_id, label)


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR Practitioner
    document: it's stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> PractitionerModel:
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            practitioner = PractitionerModel(
                tenant_id=org_id,
                created_by=created_by,
                user_id=user_id_of(document),
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(practitioner)
            try:
                await session.commit()
                await session.refresh(practitioner)
            except Exception:
                await session.rollback()
                raise
            return practitioner

    async def patch_full(
        self,
        practitioner_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt. `user_id` is deliberately not touched — it is immutable
        (the service rejects a patch that would change it)."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(
                    PractitionerModel.practitioner_id == practitioner_id
                )
            )
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None

            await _validate_local_references(session, practitioner.tenant_id, document)

            practitioner.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(practitioner, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(practitioner, rel, rows[rel])
            if updated_by is not None:
                practitioner.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(practitioner)
            except Exception:
                await session.rollback()
                raise
            return practitioner
