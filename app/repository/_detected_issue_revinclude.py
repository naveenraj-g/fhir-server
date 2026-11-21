"""`_revinclude=DetectedIssue:...` declarations for the registries of the resources a
DetectedIssue points at (Patient, Practitioner, PractitionerRole).

Kept in one neutral module that imports the DetectedIssue registry lazily, so the
registries don't import each other at load (same arrangement as `_risk_assessment_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_issue_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """DetectedIssue:<param> — issues whose `prefix` column reference points at one of
    the matched rows of `resource_type` (`patient` for a Patient, `author` for a Practitioner / PractitionerRole)."""

    async def fetch(session, ctx, rows):
        from app.repository.detected_issue.search import revinclude_issues_via_column

        return await revinclude_issues_via_column(prefix, resource_type, key)(session, ctx, rows)

    return tuple(IncludeTarget("DetectedIssue", param, resource_type, fetch, reverse=True) for param in params)


def reference_issue_revincludes(param: str, resource_type: str, key) -> tuple[IncludeTarget, ...]:
    """DetectedIssue:<param> (`problem` for a Condition / AllergyIntolerance, `investigation`
    for a RiskAssessment / FamilyMemberHistory / DiagnosticReport) — issues with a reference
    row pointing at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.detected_issue.search import revinclude_issues_via_reference

        return await revinclude_issues_via_reference(param, resource_type, key)(session, ctx, rows)

    return (IncludeTarget("DetectedIssue", param, resource_type, fetch, reverse=True),)
