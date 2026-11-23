"""`_revinclude=MedicationStatement:...` declarations for the registries of the resources a
MedicationStatement points at (`subject` / `patient`: Patient, Group; `context`: Encounter,
EpisodeOfCare; `source`: Practitioner, PractitionerRole, Organization, Patient, RelatedPerson;
`medication`: Medication; `part-of`: Observation, Procedure).

Kept in one neutral module that imports the MedicationStatement registry lazily, so the
registries don't import each other at load (same arrangement as `_medication_request_revinclude`).
"""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_medication_statement_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationStatement:<param> - statements whose `prefix` column reference points at one of
    the matched rows of `resource_type` (`subject` and `patient` for a Patient, `context`,
    `source`, `medication`)."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_statement.search import (
            revinclude_statements_via_column,
        )

        return await revinclude_statements_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("MedicationStatement", param, resource_type, fetch, reverse=True)
        for param in params
    )


def reference_medication_statement_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationStatement:part-of - statements with a reference row of `param` pointing at one
    of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_statement.search import (
            revinclude_statements_via_reference,
        )

        return await revinclude_statements_via_reference(param, resource_type, key)(
            session, ctx, rows
        )

    return (
        IncludeTarget("MedicationStatement", param, resource_type, fetch, reverse=True),
    )
