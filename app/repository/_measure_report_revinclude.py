"""`_revinclude=MeasureReport:...` declarations for the registries of the resources a
MeasureReport points at: `subject` / `patient` (Patient, Group, Practitioner, PractitionerRole,
RelatedPerson, Location), `reporter` (Practitioner, PractitionerRole, Location, Organization) and
`measure` (Measure, resolved through the canonical URL - declared by Measure's own registry).

Kept in one neutral module that imports the MeasureReport registry lazily, so the registries
don't import each other at load (same arrangement as `_questionnaire_response_revinclude`).
"""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_measure_report_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MeasureReport:<param> - reports whose `prefix` column reference (`subject`, `reporter`)
    points at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.measure_report.search import revinclude_reports_via_column

        return await revinclude_reports_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("MeasureReport", param, resource_type, fetch, reverse=True)
        for param in params
    )


def measure_measure_report_revincludes(key_url, key_id) -> tuple[IncludeTarget, ...]:
    """MeasureReport:measure - reports whose canonical URL resolves to one of the matched
    Measures (by url / `url|version` / the public id). Declared on the Measure registry."""

    async def fetch(session, ctx, rows):
        from app.repository.measure_report.search import revinclude_reports_via_measure

        return await revinclude_reports_via_measure(key_url, key_id)(session, ctx, rows)

    return (IncludeTarget("MeasureReport", "measure", "Measure", fetch, reverse=True),)
