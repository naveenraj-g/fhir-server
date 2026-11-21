"""`_revinclude=ImmunizationEvaluation:...` declarations for the registries of the
resources an ImmunizationEvaluation points at (Patient, Immunization).

Kept in one neutral module that imports the ImmunizationEvaluation registry lazily, so
the registries don't import each other at load (same arrangement as
`_immunization_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_evaluation_revincludes(
    param: str, prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """ImmunizationEvaluation:patient / :immunization-event — evaluations whose column
    reference points at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.immunization_evaluation.search import (
            revinclude_evaluations_via_column,
        )

        return await revinclude_evaluations_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return (
        IncludeTarget(
            "ImmunizationEvaluation", param, resource_type, fetch, reverse=True
        ),
    )
