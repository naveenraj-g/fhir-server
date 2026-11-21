"""`_revinclude=DiagnosticReport:...` declarations for the registries of the
resources a DiagnosticReport points at (Patient, Location, Encounter, Practitioner,
PractitionerRole).

Kept in one neutral module that imports the DiagnosticReport registry lazily, so
the registries don't import each other at load (same arrangement as
`_procedure_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def subject_report_revincludes(
    resource_type: str, key, params: tuple[str, ...]
) -> tuple[IncludeTarget, ...]:
    """DiagnosticReport:subject (and the narrowed :patient for a Patient) — reports
    whose subject is one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.diagnostic_report.search import (
            revinclude_reports_via_column,
        )

        return await revinclude_reports_via_column("subject", resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("DiagnosticReport", param, resource_type, fetch, reverse=True)
        for param in params
    )


def performer_report_revincludes(resource_type: str, key) -> tuple[IncludeTarget, ...]:
    """DiagnosticReport:performer and :results-interpreter — reports with a performer /
    results interpreter that is one of the matched rows of `resource_type`."""

    def make(param: str):
        async def fetch(session, ctx, rows):
            from app.repository.diagnostic_report.search import (
                revinclude_reports_via_performer,
            )

            return await revinclude_reports_via_performer(param, resource_type, key)(
                session, ctx, rows
            )

        return fetch

    return tuple(
        IncludeTarget(
            "DiagnosticReport", param, resource_type, make(param), reverse=True
        )
        for param in ("performer", "results-interpreter")
    )


def encounter_report_revincludes(key) -> tuple[IncludeTarget, ...]:
    """DiagnosticReport:encounter — reports ordered as part of one of the matched
    Encounters."""

    async def fetch(session, ctx, rows):
        from app.repository.diagnostic_report.search import (
            revinclude_reports_via_column,
        )

        return await revinclude_reports_via_column("encounter", "Encounter", key)(
            session, ctx, rows
        )

    return (
        IncludeTarget(
            "DiagnosticReport", "encounter", "Encounter", fetch, reverse=True
        ),
    )


def result_report_revincludes(key) -> tuple[IncludeTarget, ...]:
    """DiagnosticReport:result — reports whose `result` includes one of the matched
    Observations."""

    async def fetch(session, ctx, rows):
        from app.repository.diagnostic_report.search import (
            revinclude_reports_via_reference,
        )

        return await revinclude_reports_via_reference("result", "Observation", key)(
            session, ctx, rows
        )

    return (
        IncludeTarget("DiagnosticReport", "result", "Observation", fetch, reverse=True),
    )
