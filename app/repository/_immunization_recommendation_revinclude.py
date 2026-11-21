"""`_revinclude=ImmunizationRecommendation:...` declarations for the registries of the
resources an ImmunizationRecommendation points at (Patient, Immunization).

Kept in one neutral module that imports the ImmunizationRecommendation registry
lazily, so the registries don't import each other at load (same arrangement as
`_immunization_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def patient_recommendation_revincludes(key) -> tuple[IncludeTarget, ...]:
    """ImmunizationRecommendation:patient — recommendations for one of the matched
    Patients."""

    async def fetch(session, ctx, rows):
        from app.repository.immunization_recommendation.search import revinclude_recommendations_via_patient

        return await revinclude_recommendations_via_patient(key)(session, ctx, rows)

    return (IncludeTarget("ImmunizationRecommendation", "patient", "Patient", fetch, reverse=True),)


def support_recommendation_revincludes(key) -> tuple[IncludeTarget, ...]:
    """ImmunizationRecommendation:support — recommendations supported by one of the
    matched Immunizations."""

    async def fetch(session, ctx, rows):
        from app.repository.immunization_recommendation.search import revinclude_recommendations_via_reference

        return await revinclude_recommendations_via_reference("support", "Immunization", key)(session, ctx, rows)

    return (IncludeTarget("ImmunizationRecommendation", "support", "Immunization", fetch, reverse=True),)
