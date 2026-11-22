from sqlalchemy import select

from app.core.logging import get_logger
from app.models.medication import MedicationModel

from ._indexer import index_columns, index_rows, local_references
from ._shared import INDEX_RELATIONSHIPS, _validate_reference, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


async def _validate_local_references(session, tenant_id: str, document: dict) -> None:
    """Existence-check every relative local reference in the document
    (identifier assigners, manufacturer, Medication ingredients), scoped to the caller's org — 422 if one does not resolve."""
    for label, resource_type, ref in local_references(document):
        await _validate_reference(
            session, tenant_id, resource_type, int(ref.split("/")[1]), label
        )


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR Medication
    document: it is stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> MedicationModel:
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            medication = MedicationModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(medication)
            try:
                await session.commit()
                await session.refresh(medication)
            except Exception:
                await session.rollback()
                raise
            return medication

    async def patch_full(
        self,
        medication_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> MedicationModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationModel).where(
                    MedicationModel.medication_id == medication_id
                )
            )
            medication = (await session.execute(stmt)).scalars().first()
            if not medication:
                return None

            await _validate_local_references(session, medication.tenant_id, document)

            medication.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(medication, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(medication, rel, rows[rel])
            if updated_by is not None:
                medication.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(medication)
            except Exception:
                await session.rollback()
                raise
            return medication
