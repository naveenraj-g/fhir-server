"""`_revinclude=Immunization:...` declarations for the registries of the
resources an Immunization points at (Patient, Location, Practitioner,
PractitionerRole, Condition, DiagnosticReport).

Kept in one neutral module that imports the Immunization registry lazily, so
the registries don't import each other at load (same arrangement as
`_diagnostic_report_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_immunization_revincludes(
    param: str, prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Immunization:patient / :location / :manufacturer — immunizations whose column
    reference points at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.immunization.search import (
            revinclude_immunizations_via_column,
        )

        return await revinclude_immunizations_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return (IncludeTarget("Immunization", param, resource_type, fetch, reverse=True),)


def performer_immunization_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Immunization:performer — immunizations with a performer actor that is one of
    the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.models.immunization import ImmunizationPerformer
        from app.repository.immunization.search import (
            revinclude_immunizations_via_child,
        )

        return await revinclude_immunizations_via_child(
            ImmunizationPerformer, resource_type, key
        )(session, ctx, rows)

    return (
        IncludeTarget("Immunization", "performer", resource_type, fetch, reverse=True),
    )


def reason_immunization_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Immunization:reason-reference — immunizations given because of one of the
    matched Conditions / DiagnosticReports."""

    async def fetch(session, ctx, rows):
        from app.models.immunization import ImmunizationReasonReference
        from app.repository.immunization.search import (
            revinclude_immunizations_via_child,
        )

        return await revinclude_immunizations_via_child(
            ImmunizationReasonReference, resource_type, key
        )(session, ctx, rows)

    return (
        IncludeTarget(
            "Immunization", "reason-reference", resource_type, fetch, reverse=True
        ),
    )
