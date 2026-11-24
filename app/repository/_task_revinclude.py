"""`_revinclude=Task:...` declarations for the registries of the resources a Task points at
(`subject` / `patient`: Patient; `encounter`: Encounter; `owner`: Practitioner, PractitionerRole,
Organization, CareTeam, HealthcareService, Patient, RelatedPerson; `requester`: Practitioner,
PractitionerRole, Organization, Patient, RelatedPerson).

Kept in one neutral module that imports the Task registry lazily, so the registries do not import
each other at load (same arrangement as `_goal_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_task_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Task:<param> - tasks whose `prefix` column reference (`for`, `encounter`, `owner`,
    `requester`) points at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.task.search import revinclude_tasks_via_column

        return await revinclude_tasks_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Task", param, resource_type, fetch, reverse=True)
        for param in params
    )
