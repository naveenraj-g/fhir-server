"""`_revinclude=MedicationDispense:...` declarations for the registries of the resources a
MedicationDispense points at (`subject` / `patient`: Patient, Group; `context`: Encounter,
EpisodeOfCare; `medication`: Medication; `destination`: Location; `performer`: Practitioner,
PractitionerRole, Organization, Patient, RelatedPerson; `prescription`: MedicationRequest;
`receiver`: Practitioner, Patient; `responsibleparty`: Practitioner, PractitionerRole).

Kept in one neutral module that imports the MedicationDispense registry lazily, so the
registries don't import each other at load (same arrangement as `_medication_administration_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_medication_dispense_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationDispense:<param> - dispenses whose `prefix` column reference points at one of
    the matched rows of `resource_type` (`subject` and `patient` for a Patient, `context`,
    `medication`, `request`)."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_dispense.search import (
            revinclude_dispenses_via_column,
        )

        return await revinclude_dispenses_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("MedicationDispense", param, resource_type, fetch, reverse=True)
        for param in params
    )


def reference_medication_dispense_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationDispense:performer / :device - dispenses with a reference row of `param` pointing at one
    of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_dispense.search import (
            revinclude_dispenses_via_reference,
        )

        return await revinclude_dispenses_via_reference(param, resource_type, key)(
            session, ctx, rows
        )

    return (
        IncludeTarget("MedicationDispense", param, resource_type, fetch, reverse=True),
    )
