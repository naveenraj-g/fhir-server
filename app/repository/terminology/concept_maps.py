from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.models.terminology.terminology import TerminologyCodeSystem, TerminologyConcept, TerminologyConceptMap


class _ConceptMapsMixin:
    async def list_concept_maps(
        self, source_system: str | None, target_system: str | None, limit: int, offset: int
    ) -> tuple[int, list[tuple]]:
        SrcConceptAlias = aliased(TerminologyConcept, name="src_concept")
        TgtConceptAlias = aliased(TerminologyConcept, name="tgt_concept")
        SrcCSAlias = aliased(TerminologyCodeSystem, name="src_cs")
        TgtCSAlias = aliased(TerminologyCodeSystem, name="tgt_cs")

        async with self.session_factory() as session:
            stmt = (
                select(TerminologyConceptMap, SrcConceptAlias, SrcCSAlias, TgtConceptAlias, TgtCSAlias)
                .join(SrcConceptAlias, TerminologyConceptMap.source_concept_id == SrcConceptAlias.id)
                .join(SrcCSAlias, SrcConceptAlias.code_system_id == SrcCSAlias.id)
                .join(TgtConceptAlias, TerminologyConceptMap.target_concept_id == TgtConceptAlias.id)
                .join(TgtCSAlias, TgtConceptAlias.code_system_id == TgtCSAlias.id)
            )
            if source_system:
                stmt = stmt.where(SrcCSAlias.canonical_url == source_system)
            if target_system:
                stmt = stmt.where(TgtCSAlias.canonical_url == target_system)

            # Count over the same filtered/joined stmt (pre sort/limit/offset),
            # not a bare count of the whole table — otherwise `total` ignores
            # source_system/target_system entirely and overstates how many
            # rows actually match under pagination.
            count = await session.scalar(
                select(func.count()).select_from(stmt.subquery())
            )
            rows = await session.execute(
                stmt.order_by(TerminologyConceptMap.confidence.desc()).limit(limit).offset(offset)
            )
            return count or 0, list(rows.all())

    async def add_concept_map(
        self,
        source_concept_id: int,
        target_concept_id: int,
        mapping_type: str | None,
        confidence: float | None,
    ) -> bool:
        """Returns True if inserted, False if already exists."""
        async with self.session_factory() as session:
            exists = await session.scalar(
                select(func.count())
                .select_from(TerminologyConceptMap)
                .where(TerminologyConceptMap.source_concept_id == source_concept_id)
                .where(TerminologyConceptMap.target_concept_id == target_concept_id)
                .where(TerminologyConceptMap.mapping_type == mapping_type)
            )
            if exists:
                return False
            session.add(
                TerminologyConceptMap(
                    source_concept_id=source_concept_id,
                    target_concept_id=target_concept_id,
                    mapping_type=mapping_type,
                    confidence=confidence,
                )
            )
            await session.commit()
            return True
