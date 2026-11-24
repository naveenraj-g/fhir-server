from sqlalchemy import select

from app.core.logging import get_logger
from app.models.medication_knowledge import MedicationKnowledgeModel

from app.repository._reference_check import validate_local_references
from ._indexer import index_columns, index_rows
from ._shared import INDEX_RELATIONSHIPS, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR MedicationKnowledge
    document: it is stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> MedicationKnowledgeModel:
        async with self.session_factory() as session:
            await validate_local_references(session, org_id, document)
            medication_knowledge = MedicationKnowledgeModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(medication_knowledge)
            try:
                await session.commit()
                await session.refresh(medication_knowledge)
            except Exception:
                await session.rollback()
                raise
            return medication_knowledge

    async def patch_full(
        self,
        medication_knowledge_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> MedicationKnowledgeModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationKnowledgeModel).where(
                    MedicationKnowledgeModel.medication_knowledge_id
                    == medication_knowledge_id
                )
            )
            medication_knowledge = (await session.execute(stmt)).scalars().first()
            if not medication_knowledge:
                return None

            await validate_local_references(
                session, medication_knowledge.tenant_id, document
            )

            medication_knowledge.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(medication_knowledge, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(medication_knowledge, rel, rows[rel])
            if updated_by is not None:
                medication_knowledge.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(medication_knowledge)
            except Exception:
                await session.rollback()
                raise
            return medication_knowledge
