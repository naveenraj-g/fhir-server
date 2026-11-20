"""`_revinclude=Condition:...` declarations for the registries of the resources a
Condition points at (Patient, Practitioner, PractitionerRole, RelatedPerson,
Encounter).

Kept in one neutral module that imports the Condition registry lazily, so the
registries don't import each other at load (same arrangement as
`_allergy_intolerance_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def subject_condition_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Condition:subject / :patient — conditions whose subject is one of the
    matched Patients."""

    async def fetch(session, ctx, rows):
        from app.repository.condition.search import revinclude_conditions_via_column

        return await revinclude_conditions_via_column("subject", "Patient", key)(session, ctx, rows)

    return tuple(IncludeTarget("Condition", param, "Patient", fetch, reverse=True) for param in ("subject", "patient"))


def asserter_condition_revincludes(resource_type: str, key) -> tuple[IncludeTarget, ...]:
    """Condition:asserter — conditions whose asserter is one of the matched rows
    of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.condition.search import revinclude_conditions_via_column

        return await revinclude_conditions_via_column("asserter", resource_type, key)(session, ctx, rows)

    return (IncludeTarget("Condition", "asserter", resource_type, fetch, reverse=True),)


def encounter_condition_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Condition:encounter — conditions created as part of one of the matched
    Encounters."""

    async def fetch(session, ctx, rows):
        from app.repository.condition.search import revinclude_conditions_via_column

        return await revinclude_conditions_via_column("encounter", "Encounter", key)(session, ctx, rows)

    return (IncludeTarget("Condition", "encounter", "Encounter", fetch, reverse=True),)
