"""`_revinclude=Specimen:...` declarations for the registries of the resources a Specimen
points at (Patient, Location, Practitioner, PractitionerRole).

Kept in one neutral module that imports the Specimen registry lazily, so the registries don't
import each other at load (same arrangement as `_detected_issue_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_specimen_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Specimen:<param> — specimens whose `prefix` column reference points at one of the matched
    rows of `resource_type` (`subject` and `patient` for a Patient, `subject` for a Location,
    `collector` for a Practitioner / PractitionerRole)."""

    async def fetch(session, ctx, rows):
        from app.repository.specimen.search import revinclude_specimens_via_column

        return await revinclude_specimens_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Specimen", param, resource_type, fetch, reverse=True)
        for param in params
    )
