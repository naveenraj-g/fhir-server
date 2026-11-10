from sqlalchemy import select, update

from app.models.terminology.terminology import (
    TerminologyClosureConcept,
    TerminologyClosureTable,
    TerminologyCodeSystem,
    TerminologyConcept,
)


class _ClosureMixin:
    """Backs ConceptMap's `$closure` operation's server-side state — see
    docs/terminology-service/09-fhir-r4-terminology-standard-reference.md
    §4.4 and TerminologyClosureTable/TerminologyClosureConcept's own
    docstrings (app/models/terminology/terminology.py) for the shape."""

    async def get_closure_table(self, name: str) -> TerminologyClosureTable | None:
        async with self.session_factory() as session:
            row = await session.execute(
                select(TerminologyClosureTable).where(
                    TerminologyClosureTable.name == name
                )
            )
            return row.scalar_one_or_none()

    async def create_closure_table(self, name: str) -> TerminologyClosureTable:
        async with self.session_factory() as session:
            table = TerminologyClosureTable(name=name, version=0)
            session.add(table)
            await session.commit()
            await session.refresh(table)
            return table

    async def reinitialize_closure_table(self, closure_table_id: int) -> None:
        """(Re)initialize: wipe every member, reset version to 0 — same
        meaning the spec gives "zero concepts on initialization"."""
        async with self.session_factory() as session:
            await session.execute(
                TerminologyClosureConcept.__table__.delete().where(
                    TerminologyClosureConcept.closure_table_id == closure_table_id
                )
            )
            await session.execute(
                update(TerminologyClosureTable)
                .where(TerminologyClosureTable.id == closure_table_id)
                .values(version=0)
            )
            await session.commit()

    async def get_closure_members(
        self, closure_table_id: int
    ) -> list[tuple[TerminologyConcept, TerminologyCodeSystem]]:
        async with self.session_factory() as session:
            rows = await session.execute(
                select(TerminologyConcept, TerminologyCodeSystem)
                .join(
                    TerminologyClosureConcept,
                    TerminologyClosureConcept.concept_id == TerminologyConcept.id,
                )
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyClosureConcept.closure_table_id == closure_table_id)
            )
            return list(rows.all())

    async def add_closure_members(
        self, closure_table_id: int, concept_ids: list[int], new_version: int
    ) -> None:
        """Adds each concept_id as a member at `new_version` and bumps the
        table's own version column to match — one commit, so a caller never
        observes the members added without the version bump reflecting it
        (or vice versa)."""
        async with self.session_factory() as session:
            for concept_id in concept_ids:
                session.add(
                    TerminologyClosureConcept(
                        closure_table_id=closure_table_id,
                        concept_id=concept_id,
                        added_at_version=new_version,
                    )
                )
            await session.execute(
                update(TerminologyClosureTable)
                .where(TerminologyClosureTable.id == closure_table_id)
                .values(version=new_version)
            )
            await session.commit()

    async def get_closure_additions_since(
        self, closure_table_id: int, since_version: int
    ) -> list[tuple[TerminologyConcept, TerminologyCodeSystem, int]]:
        """Every member added at a version strictly greater than
        `since_version` — the resync case (`$closure` called with
        `version` set, no `concept`). `since_version=0` therefore returns
        every member the table has ever had, since every real version
        starts at 1."""
        async with self.session_factory() as session:
            rows = await session.execute(
                select(
                    TerminologyConcept,
                    TerminologyCodeSystem,
                    TerminologyClosureConcept.added_at_version,
                )
                .join(
                    TerminologyClosureConcept,
                    TerminologyClosureConcept.concept_id == TerminologyConcept.id,
                )
                .join(
                    TerminologyCodeSystem,
                    TerminologyConcept.code_system_id == TerminologyCodeSystem.id,
                )
                .where(TerminologyClosureConcept.closure_table_id == closure_table_id)
                .where(TerminologyClosureConcept.added_at_version > since_version)
            )
            return list(rows.all())
