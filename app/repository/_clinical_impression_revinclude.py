"""`_revinclude=ClinicalImpression:...` declarations for the registries of the resources a
ClinicalImpression points at (Patient, Encounter, Practitioner, PractitionerRole, Condition,
AllergyIntolerance, RiskAssessment, FamilyMemberHistory, DiagnosticReport).

Kept in one neutral module that imports the ClinicalImpression registry lazily, so the
registries don't import each other at load (same arrangement as `_risk_assessment_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_impression_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """ClinicalImpression:<param> — impressions whose `prefix` column reference points at one of
    the matched rows of `resource_type` (`subject` and `patient` for a Patient, `encounter` for
    an Encounter, `assessor` for a Practitioner / PractitionerRole)."""

    async def fetch(session, ctx, rows):
        from app.repository.clinical_impression.search import revinclude_impressions_via_column

        return await revinclude_impressions_via_column(prefix, resource_type, key)(session, ctx, rows)

    return tuple(IncludeTarget("ClinicalImpression", param, resource_type, fetch, reverse=True) for param in params)


def reference_impression_revincludes(param: str, resource_type: str, key) -> tuple[IncludeTarget, ...]:
    """ClinicalImpression:<param> (`problem` for a Condition / AllergyIntolerance, `investigation`
    for a RiskAssessment / FamilyMemberHistory / DiagnosticReport) — impressions with a reference
    row pointing at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.clinical_impression.search import revinclude_impressions_via_reference

        return await revinclude_impressions_via_reference(param, resource_type, key)(session, ctx, rows)

    return (IncludeTarget("ClinicalImpression", param, resource_type, fetch, reverse=True),)
