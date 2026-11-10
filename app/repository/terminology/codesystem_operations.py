from sqlalchemy import select

from app.models.terminology.terminology import (
    TerminologyConceptSynonym,
    TerminologyConceptTranslation,
)


class _CodeSystemOperationsMixin:
    """Backs CodeSystem's `$lookup` operation's `designation[]` output — see
    docs/terminology-service/09-fhir-r4-terminology-standard-reference.md
    §2.6. Separate from `_ConceptsMixin.lookup_concept()` (which resolves
    the concept itself) since `$lookup` the OPERATION needs strictly more
    than `lookup_concept()` the existing helper already returns."""

    async def get_concept_synonyms(
        self, concept_id: int
    ) -> list[TerminologyConceptSynonym]:
        async with self.session_factory() as session:
            rows = await session.execute(
                select(TerminologyConceptSynonym).where(
                    TerminologyConceptSynonym.concept_id == concept_id
                )
            )
            return list(rows.scalars().all())

    async def get_concept_translations(
        self, concept_id: int
    ) -> list[TerminologyConceptTranslation]:
        async with self.session_factory() as session:
            rows = await session.execute(
                select(TerminologyConceptTranslation).where(
                    TerminologyConceptTranslation.concept_id == concept_id
                )
            )
            return list(rows.scalars().all())
