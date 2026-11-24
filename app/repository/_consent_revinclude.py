"""`_revinclude=Consent:...` declarations for the registries of the resources a Consent points at
(`patient`: Patient; `consentor`: Organization, Patient, Practitioner, RelatedPerson,
PractitionerRole; `organization`: Organization; `actor`: Device, Group, CareTeam, Organization,
Patient, Practitioner, RelatedPerson, PractitionerRole; `source-reference`: DocumentReference,
QuestionnaireResponse).

Kept in one neutral module that imports the Consent registry lazily, so the registries do not
import each other at load (same arrangement as `_task_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_consent_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Consent:<param> - consents whose `prefix` column reference (`patient`, `source`) points at
    one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.consent.search import revinclude_consents_via_column

        return await revinclude_consents_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Consent", param, resource_type, fetch, reverse=True)
        for param in params
    )


def reference_consent_revincludes(
    params: tuple[str, ...], resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Consent:<param> - consents with a row of that `param` (`consentor`, `organization`,
    `actor`) in the reference table pointing at one of the matched rows of `resource_type`."""

    def build(param: str):
        async def fetch(session, ctx, rows):
            from app.repository.consent.search import revinclude_consents_via_reference

            return await revinclude_consents_via_reference(param, resource_type, key)(
                session, ctx, rows
            )

        return IncludeTarget("Consent", param, resource_type, fetch, reverse=True)

    return tuple(build(param) for param in params)
