"""`_revinclude=Goal:...` declarations for the registries of the resources a Goal points at
(`subject` / `patient`: Patient, Group, Organization).

Kept in one neutral module that imports the Goal registry lazily, so the registries do not import
each other at load (same arrangement as `_care_team_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_goal_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Goal:<param> - goals whose `subject` points at one of the matched rows of `resource_type`
    (`subject` and `patient` for a Patient, `subject` for a Group or an Organization)."""

    async def fetch(session, ctx, rows):
        from app.repository.goal.search import revinclude_goals_via_column

        return await revinclude_goals_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Goal", param, resource_type, fetch, reverse=True)
        for param in params
    )
