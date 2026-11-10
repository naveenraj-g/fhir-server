from sqlalchemy import select

from app.models.terminology.terminology import (
    TerminologyCodeSystem,
    TerminologyConcept,
    TerminologyConceptMap,
)


class _ConceptMapOperationsMixin:
    """Backs ConceptMap's `$translate` (`reverse=true` direction) — see
    docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §4.3.
    The forward direction (source_concept_id -> target) is already covered
    by `_ValidationMixin.get_translations()`
    (app/repository/terminology/validation.py); this is its mirror for
    `reverse=true`, where the caller's given code is on the TARGET side of
    stored rows and the SOURCE side is what should be returned instead."""

    async def get_reverse_translations(
        self, target_concept_id: int, source_system: str | None
    ) -> list[tuple[TerminologyConceptMap, TerminologyConcept, TerminologyCodeSystem]]:
        async with self.session_factory() as session:
            stmt = (
                select(TerminologyConceptMap, TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyConcept,
                    TerminologyConceptMap.source_concept_id == TerminologyConcept.id,
                )
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyConceptMap.target_concept_id == target_concept_id)
            )
            if source_system:
                stmt = stmt.where(TerminologyCodeSystem.canonical_url == source_system)
            rows = await session.execute(
                stmt.order_by(TerminologyConceptMap.confidence.desc())
            )
            return list(rows.all())
