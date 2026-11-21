from sqlalchemy import select

from app.core.logging import get_logger
from app.models.encounter import EncounterModel

from ._indexer import index_columns, index_rows, local_references
from ._shared import INDEX_RELATIONSHIPS, _validate_reference, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


async def _validate_local_references(session, tenant_id: str, document: dict) -> None:
    """Existence-check every relative local reference in the document
    (identifier.assigner, subject, partOf, serviceProvider, appointment, participant
    individuals and locations of a modeled type, hospitalization.origin/destination), scoped to
    the caller's org — 422 if one does not resolve."""
    for label, resource_type, ref in local_references(document):
        await _validate_reference(
            session, tenant_id, resource_type, int(ref.split("/")[1]), label
        )


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR Encounter
    document: it is stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> EncounterModel:
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            encounter = EncounterModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(encounter)
            try:
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise
            return encounter

    async def patch_full(
        self,
        encounter_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> EncounterModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EncounterModel).where(
                    EncounterModel.encounter_id == encounter_id
                )
            )
            encounter = (await session.execute(stmt)).scalars().first()
            if not encounter:
                return None

            await _validate_local_references(session, encounter.tenant_id, document)

            encounter.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(encounter, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(encounter, rel, rows[rel])
            if updated_by is not None:
                encounter.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise
            return encounter
