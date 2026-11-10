from sqlalchemy import select

from app.models.terminology.terminology import (
    TerminologyConcept,
    TerminologyRelationship,
)


class _CapabilitiesMixin:
    """Backs the `TerminologyCapabilities` resource (see
    docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §6)
    — specifically its `codeSystem[].subsumption` flag, which has to say
    whether THIS code system actually has IS-A hierarchy data (not just
    whether `$subsumes` exists as an operation at all — it always does;
    whether it ever returns anything other than `not-subsumed` for a given
    code system depends on whether `TerminologyRelationship` rows exist for
    it, which today is SNOMED CT only)."""

    async def code_systems_with_hierarchy_data(self) -> set[int]:
        """Every `code_system_id` that has at least one `is-a`
        `TerminologyRelationship` row among its own concepts."""
        async with self.session_factory() as session:
            rows = await session.execute(
                select(TerminologyConcept.code_system_id)
                .join(
                    TerminologyRelationship,
                    TerminologyRelationship.parent_concept_id == TerminologyConcept.id,
                )
                .where(TerminologyRelationship.relationship_type == "is-a")
                .distinct()
            )
            return {r[0] for r in rows}
