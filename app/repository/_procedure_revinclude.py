"""`_revinclude=Procedure:...` declarations for the registries of the resources a
Procedure points at (Patient, Practitioner, PractitionerRole, RelatedPerson,
Encounter, Location, Condition).

Kept in one neutral module that imports the Procedure registry lazily, so the
registries don't import each other at load (same arrangement as
`_condition_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def subject_procedure_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Procedure:subject / :patient — procedures whose subject is one of the
    matched Patients."""

    async def fetch(session, ctx, rows):
        from app.repository.procedure.search import revinclude_procedures_via_column

        return await revinclude_procedures_via_column("subject", "Patient", key)(session, ctx, rows)

    return tuple(IncludeTarget("Procedure", param, "Patient", fetch, reverse=True) for param in ("subject", "patient"))


def performer_procedure_revincludes(resource_type: str, key) -> tuple[IncludeTarget, ...]:
    """Procedure:performer — procedures with a performer actor that is one of the
    matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.models.procedure import ProcedurePerformer
        from app.repository.procedure.search import revinclude_procedures_via_child

        return await revinclude_procedures_via_child(ProcedurePerformer, resource_type, key)(session, ctx, rows)

    return (IncludeTarget("Procedure", "performer", resource_type, fetch, reverse=True),)


def encounter_procedure_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Procedure:encounter — procedures created as part of one of the matched
    Encounters."""

    async def fetch(session, ctx, rows):
        from app.repository.procedure.search import revinclude_procedures_via_column

        return await revinclude_procedures_via_column("encounter", "Encounter", key)(session, ctx, rows)

    return (IncludeTarget("Procedure", "encounter", "Encounter", fetch, reverse=True),)


def location_procedure_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Procedure:location — procedures that happened at one of the matched Locations."""

    async def fetch(session, ctx, rows):
        from app.repository.procedure.search import revinclude_procedures_via_column

        return await revinclude_procedures_via_column("location", "Location", key)(session, ctx, rows)

    return (IncludeTarget("Procedure", "location", "Location", fetch, reverse=True),)


def reason_procedure_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Procedure:reason-reference — procedures whose reason is one of the matched
    Conditions."""

    async def fetch(session, ctx, rows):
        from app.models.procedure import ProcedureReference
        from app.repository.procedure.search import revinclude_procedures_via_child

        return await revinclude_procedures_via_child(
            ProcedureReference, "Condition", key, ProcedureReference.param == "reason-reference"
        )(session, ctx, rows)

    return (IncludeTarget("Procedure", "reason-reference", "Condition", fetch, reverse=True),)
