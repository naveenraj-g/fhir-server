"""`_revinclude=MedicationAdministration:...` declarations for the registries of the resources a
MedicationAdministration points at (`subject` / `patient`: Patient, Group; `context`: Encounter,
EpisodeOfCare; `medication`: Medication; `request`: MedicationRequest; `performer`: Practitioner,
PractitionerRole, Patient, RelatedPerson).

Kept in one neutral module that imports the MedicationAdministration registry lazily, so the
registries don't import each other at load (same arrangement as `_medication_statement_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_medication_administration_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationAdministration:<param> - administrations whose `prefix` column reference points at one of
    the matched rows of `resource_type` (`subject` and `patient` for a Patient, `context`,
    `medication`, `request`)."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_administration.search import (
            revinclude_administrations_via_column,
        )

        return await revinclude_administrations_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget(
            "MedicationAdministration", param, resource_type, fetch, reverse=True
        )
        for param in params
    )


def reference_medication_administration_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationAdministration:performer / :device - administrations with a reference row of `param` pointing at one
    of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_administration.search import (
            revinclude_administrations_via_reference,
        )

        return await revinclude_administrations_via_reference(
            param, resource_type, key
        )(session, ctx, rows)

    return (
        IncludeTarget(
            "MedicationAdministration", param, resource_type, fetch, reverse=True
        ),
    )
