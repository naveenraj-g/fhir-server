"""`_revinclude=MedicationRequest:...` declarations for the registries of the resources a
MedicationRequest points at (Patient, Encounter, Practitioner, PractitionerRole, RelatedPerson,
Organization, Medication).

Kept in one neutral module that imports the MedicationRequest registry lazily, so the
registries don't import each other at load (same arrangement as `_service_request_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_medication_request_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationRequest:<param> - medication requests whose `prefix` column reference points
    at one of the matched rows of `resource_type` (`subject` and `patient` for a Patient,
    `encounter` for an Encounter, `requester`, `intended-performer` (prefix `performer`),
    `intended-dispenser` (prefix `dispenser`) and `medication`)."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_request.search import (
            revinclude_medication_requests_via_column,
        )

        return await revinclude_medication_requests_via_column(
            prefix, resource_type, key
        )(session, ctx, rows)

    return tuple(
        IncludeTarget("MedicationRequest", param, resource_type, fetch, reverse=True)
        for param in params
    )
