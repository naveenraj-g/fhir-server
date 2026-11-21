"""`_revinclude=RiskAssessment:...` declarations for the registries of the resources a
RiskAssessment points at (Patient, Condition, Encounter, Practitioner, PractitionerRole).

Kept in one neutral module that imports the RiskAssessment registry lazily, so the registries
don't import each other at load (same arrangement as `_immunization_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_risk_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """RiskAssessment:<param> — assessments whose `prefix` column reference points at one of the
    matched rows of `resource_type` (`subject` and `patient` for a Patient, `condition`,
    `encounter` or `performer` for the others)."""

    async def fetch(session, ctx, rows):
        from app.repository.risk_assessment.search import (
            revinclude_assessments_via_column,
        )

        return await revinclude_assessments_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("RiskAssessment", param, resource_type, fetch, reverse=True)
        for param in params
    )
