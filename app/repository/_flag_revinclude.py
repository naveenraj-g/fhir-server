"""`_revinclude=Flag:...` declarations for the registries of the resources a Flag points at
(`subject` / `patient`: Patient, Location, Group, Organization, Practitioner, Medication,
Procedure; `encounter`: Encounter; `author`: Organization, Patient, Practitioner,
PractitionerRole).

Kept in one neutral module that imports the Flag registry lazily, so the registries do not import
each other at load (same arrangement as `_goal_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_flag_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Flag:<param> - flags whose `prefix` column reference (`subject`, `encounter`, `author`)
    points at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.flag.search import revinclude_flags_via_column

        return await revinclude_flags_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Flag", param, resource_type, fetch, reverse=True)
        for param in params
    )
