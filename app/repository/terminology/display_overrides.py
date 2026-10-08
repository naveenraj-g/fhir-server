from sqlalchemy import func, select

from app.models.terminology.terminology import (
    TerminologyAuditLog,
    TerminologyCodeSystem,
    TerminologyConcept,
    TerminologyDisplayOverride,
)


class _DisplayOverridesMixin:
    async def create_display_override(
        self,
        concept_id: int,
        org_id: str,
        display: str,
        definition: str | None,
        user_id: str | None = None,
    ) -> TerminologyDisplayOverride:
        async with self.session_factory() as session:
            override = TerminologyDisplayOverride(
                concept_id=concept_id,
                org_id=org_id,
                display=display,
                definition=definition,
                user_id=user_id,
            )
            session.add(override)
            await session.flush()
            session.add(TerminologyAuditLog(
                action="display_override.created",
                display_override_id=override.id,
                performed_by=user_id,
                new_value={
                    "concept_id": concept_id,
                    "display": display,
                    "definition": definition,
                    "org_id": org_id,
                },
            ))
            await session.commit()
            await session.refresh(override)
            return override

    async def get_display_override(
        self, override_id: int, org_id: str
    ) -> tuple[TerminologyDisplayOverride, TerminologyConcept, TerminologyCodeSystem] | None:
        async with self.session_factory() as session:
            row = await session.execute(
                select(TerminologyDisplayOverride, TerminologyConcept, TerminologyCodeSystem)
                .join(TerminologyConcept, TerminologyDisplayOverride.concept_id == TerminologyConcept.id)
                .join(TerminologyCodeSystem, TerminologyConcept.code_system_id == TerminologyCodeSystem.id)
                .where(TerminologyDisplayOverride.id == override_id)
                .where(TerminologyDisplayOverride.org_id == org_id)
            )
            return row.first()

    async def patch_display_override(
        self,
        override_id: int,
        org_id: str,
        display: str | None,
        definition: str | None,
    ) -> tuple[TerminologyDisplayOverride, TerminologyConcept, TerminologyCodeSystem] | None:
        async with self.session_factory() as session:
            row = await session.execute(
                select(TerminologyDisplayOverride, TerminologyConcept, TerminologyCodeSystem)
                .join(TerminologyConcept, TerminologyDisplayOverride.concept_id == TerminologyConcept.id)
                .join(TerminologyCodeSystem, TerminologyConcept.code_system_id == TerminologyCodeSystem.id)
                .where(TerminologyDisplayOverride.id == override_id)
                .where(TerminologyDisplayOverride.org_id == org_id)
            )
            result = row.first()
            if result is None:
                return None
            override, concept, cs = result
            old = {"display": override.display, "definition": override.definition}
            if display is not None:
                override.display = display
            if definition is not None:
                override.definition = definition
            await session.flush()
            session.add(TerminologyAuditLog(
                action="display_override.updated",
                display_override_id=override.id,
                performed_by=override.user_id,
                old_value=old,
                new_value={"display": override.display, "definition": override.definition},
            ))
            await session.commit()
            await session.refresh(override)
            return override, concept, cs

    async def delete_display_override(self, override_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TerminologyDisplayOverride)
                .where(TerminologyDisplayOverride.id == override_id)
                .where(TerminologyDisplayOverride.org_id == org_id)
            )
            override = result.scalar_one_or_none()
            if override is None:
                return False
            session.add(TerminologyAuditLog(
                action="display_override.deleted",
                performed_by=override.user_id,
                old_value={
                    "concept_id": override.concept_id,
                    "display": override.display,
                    "definition": override.definition,
                    "org_id": override.org_id,
                },
            ))
            await session.delete(override)
            await session.commit()
            return True

    async def list_display_overrides(
        self, org_id: str, limit: int, offset: int
    ) -> tuple[int, list[tuple]]:
        async with self.session_factory() as session:
            base = (
                select(TerminologyDisplayOverride, TerminologyConcept, TerminologyCodeSystem)
                .join(TerminologyConcept, TerminologyDisplayOverride.concept_id == TerminologyConcept.id)
                .join(TerminologyCodeSystem, TerminologyConcept.code_system_id == TerminologyCodeSystem.id)
                .where(TerminologyDisplayOverride.org_id == org_id)
            )
            count_stmt = (
                select(func.count())
                .select_from(TerminologyDisplayOverride)
                .where(TerminologyDisplayOverride.org_id == org_id)
            )
            count = await session.scalar(count_stmt)
            rows = await session.execute(
                base.order_by(TerminologyDisplayOverride.id).limit(limit).offset(offset)
            )
            return count or 0, list(rows.all())
