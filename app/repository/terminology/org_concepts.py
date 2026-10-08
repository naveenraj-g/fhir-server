from sqlalchemy import func, select, text

from app.models.terminology.terminology import (
    TerminologyAuditLog,
    TerminologyCodeSystem,
    TerminologyConcept,
)


class _OrgConceptsMixin:
    async def create_org_concept(
        self,
        code_system_id: int,
        code: str,
        display: str,
        definition: str | None,
        org_id: str,
        user_id: str | None = None,
    ) -> TerminologyConcept:
        async with self.session_factory() as session:
            concept = TerminologyConcept(
                code_system_id=code_system_id,
                code=code,
                display=display,
                definition=definition,
                org_id=org_id,
                user_id=user_id,
            )
            session.add(concept)
            await session.flush()
            await session.execute(
                text(
                    "UPDATE terminology_concept SET search_vector = to_tsvector('english', :txt) WHERE id = :id"
                ),
                {"txt": f"{display} {definition or ''}".strip(), "id": concept.id},
            )
            session.add(
                TerminologyAuditLog(
                    action="org_concept.created",
                    concept_id=concept.id,
                    performed_by=user_id,
                    new_value={
                        "code": code,
                        "display": display,
                        "definition": definition,
                        "org_id": org_id,
                    },
                )
            )
            await session.commit()
            await session.refresh(concept)
            return concept

    async def get_org_concept(
        self, concept_id: int, org_id: str
    ) -> tuple[TerminologyConcept, TerminologyCodeSystem] | None:
        async with self.session_factory() as session:
            row = await session.execute(
                select(TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyConcept.id == concept_id)
                .where(TerminologyConcept.org_id == org_id)
            )
            return row.first()

    async def patch_org_concept(
        self,
        concept_id: int,
        org_id: str,
        display: str | None,
        definition: str | None,
    ) -> tuple[TerminologyConcept, TerminologyCodeSystem] | None:
        async with self.session_factory() as session:
            row = await session.execute(
                select(TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyConcept.id == concept_id)
                .where(TerminologyConcept.org_id == org_id)
            )
            result = row.first()
            if result is None:
                return None
            concept, cs = result[0], result[1]
            old = {"display": concept.display, "definition": concept.definition}
            if display is not None:
                concept.display = display
            if definition is not None:
                concept.definition = definition
            await session.flush()
            search_text = f"{concept.display} {concept.definition or ''}".strip()
            await session.execute(
                text(
                    "UPDATE terminology_concept SET search_vector = to_tsvector('english', :txt) WHERE id = :id"
                ),
                {"txt": search_text, "id": concept.id},
            )
            session.add(
                TerminologyAuditLog(
                    action="org_concept.updated",
                    concept_id=concept.id,
                    performed_by=concept.user_id,
                    old_value=old,
                    new_value={
                        "display": concept.display,
                        "definition": concept.definition,
                    },
                )
            )
            await session.commit()
            await session.refresh(concept)
            return concept, cs

    async def delete_org_concept(self, concept_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TerminologyConcept)
                .where(TerminologyConcept.id == concept_id)
                .where(TerminologyConcept.org_id == org_id)
            )
            concept = result.scalar_one_or_none()
            if concept is None:
                return False
            session.add(
                TerminologyAuditLog(
                    action="org_concept.deleted",
                    performed_by=concept.user_id,
                    old_value={
                        "code": concept.code,
                        "display": concept.display,
                        "definition": concept.definition,
                        "org_id": concept.org_id,
                    },
                )
            )
            await session.delete(concept)
            await session.commit()
            return True

    async def list_org_concepts(
        self,
        org_id: str,
        code_system_url: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[tuple]]:
        async with self.session_factory() as session:
            base = (
                select(TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyConcept.org_id == org_id)
            )
            count_stmt = (
                select(func.count())
                .select_from(TerminologyConcept)
                .where(TerminologyConcept.org_id == org_id)
            )
            if code_system_url:
                base = base.where(
                    TerminologyCodeSystem.canonical_url == code_system_url
                )
                count_stmt = (
                    select(func.count())
                    .select_from(TerminologyConcept)
                    .join(
                        TerminologyCodeSystem,
                        TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                    )
                    .where(TerminologyConcept.org_id == org_id)
                    .where(TerminologyCodeSystem.canonical_url == code_system_url)
                )
            if q:
                trgm_where = text("terminology_concept.display ILIKE :pat").bindparams(
                    pat=f"%{q}%"
                )
                base = base.where(trgm_where)
                count_stmt = count_stmt.where(trgm_where)
            count = await session.scalar(count_stmt)
            rows = await session.execute(
                base.order_by(TerminologyConcept.code).limit(limit).offset(offset)
            )
            return count or 0, list(rows.all())
