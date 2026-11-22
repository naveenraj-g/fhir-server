"""`_revinclude=Medication:...` declarations for the registries of the resources a Medication
points at (Organization for `manufacturer`).

Kept in one neutral module that imports the Medication registry lazily, so the registries
don't import each other at load (same arrangement as `_specimen_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_medication_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Medication:<param> - medications whose `prefix` column reference points at one of the
    matched rows of `resource_type` (`manufacturer` for an Organization)."""

    async def fetch(session, ctx, rows):
        from app.repository.medication.search import revinclude_medications_via_column

        return await revinclude_medications_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Medication", param, resource_type, fetch, reverse=True)
        for param in params
    )
