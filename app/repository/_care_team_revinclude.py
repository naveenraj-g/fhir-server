"""`_revinclude=CareTeam:...` declarations for the registries of the resources a CareTeam points
at (`subject` / `patient`: Patient, Group; `encounter`: Encounter; `participant`: Practitioner,
PractitionerRole, RelatedPerson, Patient, Organization, CareTeam).

Kept in one neutral module that imports the CareTeam registry lazily, so the registries don't
import each other at load (same arrangement as `_group_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_care_team_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """CareTeam:<param> - care teams whose `prefix` column reference points at one of the matched
    rows of `resource_type` (`subject` and `patient` for a Patient, `subject` for a Group,
    `encounter` for an Encounter)."""

    async def fetch(session, ctx, rows):
        from app.repository.care_team.search import revinclude_care_teams_via_column

        return await revinclude_care_teams_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("CareTeam", param, resource_type, fetch, reverse=True)
        for param in params
    )


def participant_care_team_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """CareTeam:participant - care teams with a participant whose member points at one of the
    matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.care_team.search import (
            revinclude_care_teams_via_participant,
        )

        return await revinclude_care_teams_via_participant(resource_type, key)(
            session, ctx, rows
        )

    return (
        IncludeTarget("CareTeam", "participant", resource_type, fetch, reverse=True),
    )
