"""`_revinclude=Schedule:actor` for the registries of the resources a Schedule's `actor` can
point at (Patient, RelatedPerson; Practitioner, PractitionerRole, HealthcareService and Location
declare it in their own files).

Kept in one neutral module with lazy model imports so the registries don't import each other at
load (same arrangement as `_care_team_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def actor_schedule_revincludes(resource_type: str, key) -> tuple[IncludeTarget, ...]:
    """Schedule:actor - schedules with an actor of `resource_type` pointing at one of the matched
    rows (matched on the public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        from sqlalchemy import select

        from app.models.schedule import ScheduleActor as A
        from app.models.schedule import ScheduleModel as S

        ids = {key(r) for r in rows}
        pks = select(A.schedule_pk).where(
            A.reference_type == resource_type, A.reference_id.in_(ids)
        )
        stmt = select(S).where(S.tenant_id == ctx.tenant_id, S.id.in_(pks))
        return list((await session.execute(stmt)).scalars().all())

    return (IncludeTarget("Schedule", "actor", resource_type, fetch, reverse=True),)
