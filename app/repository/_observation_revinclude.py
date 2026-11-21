"""`_revinclude=Observation:...` declarations for the registries of the resources an Observation
points at (Patient, Encounter, Practitioner, PractitionerRole, RelatedPerson, Procedure,
Immunization).

Kept in one neutral module that imports the Observation registry lazily, so the registries
don't import each other at load (same arrangement as `_detected_issue_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_observation_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Observation:<param> — observations whose `prefix` column reference points at one of the
    matched rows of `resource_type` (`subject` and `patient` for a Patient, `encounter` for an
    Encounter)."""

    async def fetch(session, ctx, rows):
        from app.repository.observation.search import revinclude_observations_via_column

        return await revinclude_observations_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Observation", param, resource_type, fetch, reverse=True)
        for param in params
    )


def reference_observation_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Observation:<param> (`performer` for a Practitioner / PractitionerRole / RelatedPerson,
    `part-of` for a Procedure / Immunization) — observations with a reference row pointing at one
    of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.observation.search import (
            revinclude_observations_via_reference,
        )

        return await revinclude_observations_via_reference(param, resource_type, key)(
            session, ctx, rows
        )

    return (IncludeTarget("Observation", param, resource_type, fetch, reverse=True),)
