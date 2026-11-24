"""`_revinclude=Communication:...` declarations for the registries of the resources a Communication
points at (`subject` / `patient`: Patient, Group; `encounter`: Encounter; `sender`: Device,
Organization, Patient, Practitioner, PractitionerRole, RelatedPerson, HealthcareService;
`recipient`: those plus Group and CareTeam).

Kept in one neutral module that imports the Communication registry lazily, so the registries do
not import each other at load (same arrangement as `_consent_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_communication_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Communication:<param> - communications whose `prefix` column reference (`subject`,
    `encounter`, `sender`) points at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.communication.search import (
            revinclude_communications_via_column,
        )

        return await revinclude_communications_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Communication", param, resource_type, fetch, reverse=True)
        for param in params
    )


def reference_communication_revincludes(
    params: tuple[str, ...], resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Communication:<param> - communications with a row of that `param` (`recipient`) in the
    reference table pointing at one of the matched rows of `resource_type`."""

    def build(param: str):
        async def fetch(session, ctx, rows):
            from app.repository.communication.search import (
                revinclude_communications_via_reference,
            )

            return await revinclude_communications_via_reference(
                param, resource_type, key
            )(session, ctx, rows)

        return IncludeTarget("Communication", param, resource_type, fetch, reverse=True)

    return tuple(build(param) for param in params)
