"""`_revinclude=EpisodeOfCare:...` declarations for the registries of the resources an EpisodeOfCare
points at (`patient`: Patient; `organization`: Organization; `care-manager`: Practitioner;
`condition`: Condition; `incoming-referral`: ServiceRequest).

Kept in one neutral module that imports the EpisodeOfCare registry lazily, so the registries don't
import each other at load (same arrangement as `_care_team_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_episode_of_care_revincludes(
    param: str, prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """EpisodeOfCare:<param> - episodes whose `prefix` column reference points at one of the
    matched rows of `resource_type` (`patient` for a Patient, `organization` for an Organization,
    `care-manager` for a Practitioner)."""

    async def fetch(session, ctx, rows):
        from app.repository.episode_of_care.search import revinclude_episodes_via_column

        return await revinclude_episodes_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return (IncludeTarget("EpisodeOfCare", param, resource_type, fetch, reverse=True),)


def reference_episode_of_care_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """EpisodeOfCare:condition / :incoming-referral - episodes with a reference row of `param`
    pointing at one of the matched rows of `resource_type` (Condition / ServiceRequest)."""

    async def fetch(session, ctx, rows):
        from app.repository.episode_of_care.search import (
            revinclude_episodes_via_reference,
        )

        return await revinclude_episodes_via_reference(param, resource_type, key)(
            session, ctx, rows
        )

    return (IncludeTarget("EpisodeOfCare", param, resource_type, fetch, reverse=True),)
