from sqlalchemy import func, select, text

from app.models.terminology.terminology import (
    TerminologyCodeSystem,
    TerminologyConcept,
    TerminologyValueSet,
    TerminologyValueSetConcept,
)


class _ValueSetsMixin:
    async def list_value_sets(
        self, q: str | None, limit: int, offset: int
    ) -> tuple[int, list[TerminologyValueSet]]:
        async with self.session_factory() as session:
            stmt = select(TerminologyValueSet).where(TerminologyValueSet.active == True)
            if q:
                pattern = f"%{q}%"
                stmt = stmt.where(
                    TerminologyValueSet.name.ilike(pattern)
                    | TerminologyValueSet.title.ilike(pattern)
                    | TerminologyValueSet.canonical_url.ilike(pattern)
                )
            count = await session.scalar(
                select(func.count()).select_from(stmt.subquery())
            )
            rows = await session.execute(
                stmt.order_by(TerminologyValueSet.name).limit(limit).offset(offset)
            )
            return count or 0, list(rows.scalars().all())

    async def get_value_set(self, value_set_id: int) -> TerminologyValueSet | None:
        async with self.session_factory() as session:
            return await session.get(TerminologyValueSet, value_set_id)

    async def expand_value_set(
        self, value_set_id: int, q: str | None, limit: int, offset: int
    ) -> tuple[int, list[tuple]]:
        async with self.session_factory() as session:
            base = (
                select(TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyValueSetConcept,
                    TerminologyValueSetConcept.concept_id == TerminologyConcept.id,
                )
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyValueSetConcept.value_set_id == value_set_id)
                .where(TerminologyValueSetConcept.active == True)
            )
            count_stmt = (
                select(func.count())
                .select_from(TerminologyConcept)
                .join(
                    TerminologyValueSetConcept,
                    TerminologyValueSetConcept.concept_id == TerminologyConcept.id,
                )
                .where(TerminologyValueSetConcept.value_set_id == value_set_id)
                .where(TerminologyValueSetConcept.active == True)
            )
            if q:
                trgm_where = text(
                    "terminology_concept.display ILIKE :pat"
                ).bindparams(pat=f"%{q}%")
                base = base.where(trgm_where)
                count_stmt = count_stmt.where(trgm_where)

            count = await session.scalar(count_stmt)
            rows = await session.execute(
                base.order_by(TerminologyConcept.display).limit(limit).offset(offset)
            )
            return count or 0, list(rows.all())
