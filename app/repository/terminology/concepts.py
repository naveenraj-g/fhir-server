from sqlalchemy import func, select, text

from app.models.terminology.terminology import TerminologyCodeSystem, TerminologyConcept


class _ConceptsMixin:
    async def search_concepts(
        self, q: str, system: str | None, limit: int, offset: int
    ) -> tuple[int, list[tuple]]:
        async with self.session_factory() as session:
            trgm_where = text(
                "terminology_concept.display ILIKE :pat"
            ).bindparams(pat=f"%{q}%")
            trgm_rank = text(
                "similarity(terminology_concept.display, :q) DESC"
            ).bindparams(q=q)
            base = (
                select(TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(trgm_where)
                .where(TerminologyConcept.active == True)
            )
            count_stmt = (
                select(func.count())
                .select_from(TerminologyConcept)
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(trgm_where)
                .where(TerminologyConcept.active == True)
            )
            if system:
                base = base.where(TerminologyCodeSystem.canonical_url == system)
                count_stmt = count_stmt.where(
                    TerminologyCodeSystem.canonical_url == system
                )
            count = await session.scalar(count_stmt)
            rows = await session.execute(
                base.order_by(trgm_rank).limit(limit).offset(offset)
            )
            return count or 0, list(rows.all())

    async def lookup_concept(
        self, system: str, code: str
    ) -> tuple[TerminologyCodeSystem | None, TerminologyConcept | None]:
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
            if result:
                concept, cs = result[0], result[1]
                return cs, concept
            return None, None
