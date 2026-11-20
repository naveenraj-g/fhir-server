"""`_revinclude=AllergyIntolerance:...` declarations for the registries of the
resources an AllergyIntolerance points at (Patient, Practitioner,
PractitionerRole, RelatedPerson).

Kept in one neutral module that imports the AllergyIntolerance registry lazily,
so the registries don't import each other at load (same arrangement as
`_encounter_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def patient_allergy_revincludes(key) -> tuple[IncludeTarget, ...]:
    """AllergyIntolerance:patient — allergies recorded for one of the matched
    Patients."""

    async def fetch(session, ctx, rows):
        from app.repository.allergy_intolerance.search import revinclude_allergies_via_column

        return await revinclude_allergies_via_column("patient", "Patient", key)(session, ctx, rows)

    return (IncludeTarget("AllergyIntolerance", "patient", "Patient", fetch, reverse=True),)


def actor_allergy_revincludes(resource_type: str, key) -> tuple[IncludeTarget, ...]:
    """AllergyIntolerance:recorder and :asserter — allergies whose recorder /
    asserter is one of the matched rows of `resource_type`."""

    def make(param: str):
        async def fetch(session, ctx, rows):
            from app.repository.allergy_intolerance.search import revinclude_allergies_via_column

            return await revinclude_allergies_via_column(param, resource_type, key)(session, ctx, rows)

        return fetch

    return tuple(
        IncludeTarget("AllergyIntolerance", param, resource_type, make(param), reverse=True)
        for param in ("recorder", "asserter")
    )
