from sqlalchemy import func, select

from app.models.terminology.terminology import (
    TerminologyCodeSystem,
    TerminologyConcept,
    TerminologyConceptMap,
    TerminologyFieldBinding,
    TerminologyValueSetConcept,
)


class _ValidationMixin:
    async def get_field_binding(
        self, resource_type: str, field_name: str
    ) -> TerminologyFieldBinding | None:
        async with self.session_factory() as session:
            row = await session.execute(
                select(TerminologyFieldBinding)
                .where(TerminologyFieldBinding.resource_type == resource_type)
                .where(TerminologyFieldBinding.field_name == field_name)
                .where(TerminologyFieldBinding.active == True)
            )
            return row.scalar_one_or_none()

    async def lookup_concept_in_value_set(
        self, value_set_id: int, system: str, code: str
    ) -> tuple[TerminologyCodeSystem | None, TerminologyConcept | None, bool]:
        """Returns (code_system, concept, in_value_set). concept may be found even if not in value set."""
        async with self.session_factory() as session:
            row = await session.execute(
                select(TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyCodeSystem.canonical_url == system)
                .where(TerminologyConcept.code == code)
            )
            result = row.first()
            if result is None:
                return None, None, False
            concept, cs = result[0], result[1]
            in_vs = await session.scalar(
                select(func.count())
                .select_from(TerminologyValueSetConcept)
                .where(TerminologyValueSetConcept.value_set_id == value_set_id)
                .where(TerminologyValueSetConcept.concept_id == concept.id)
            )
            return cs, concept, bool(in_vs)

    async def get_translations(
        self, source_concept_id: int, target_system: str | None
    ) -> list[tuple[TerminologyConceptMap, TerminologyConcept, TerminologyCodeSystem]]:
        async with self.session_factory() as session:
            stmt = (
                select(TerminologyConceptMap, TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyConcept,
                    TerminologyConceptMap.target_concept_id == TerminologyConcept.id,
                )
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyConceptMap.source_concept_id == source_concept_id)
            )
            if target_system:
                stmt = stmt.where(TerminologyCodeSystem.canonical_url == target_system)
            rows = await session.execute(
                stmt.order_by(TerminologyConceptMap.confidence.desc())
            )
            return list(rows.all())
