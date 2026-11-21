"""`_revinclude=Encounter:...` declarations for the registries of the resources
an Encounter points at (Patient, Practitioner, PractitionerRole, Location,
Organization, Appointment).

Kept in one neutral module that imports the Encounter registry lazily, so the
registries don't import each other at load (same arrangement as
`_appointment_response_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def subject_encounter_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Encounter:subject / :patient — encounters whose subject is one of the
    matched Patients."""

    async def fetch(session, ctx, rows):
        from app.repository.encounter.search import revinclude_encounters_via_column

        return await revinclude_encounters_via_column("subject", "Patient", key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("Encounter", param, "Patient", fetch, reverse=True)
        for param in ("subject", "patient")
    )


def participant_encounter_revincludes(
    resource_type: str, key, params: tuple[str, ...]
) -> tuple[IncludeTarget, ...]:
    """Encounter:participant (and :practitioner for a Practitioner) —
    encounters with a participant individual of `resource_type` pointing at one
    of the matched rows."""

    async def fetch(session, ctx, rows):
        from app.models.encounter import EncounterParticipant
        from app.repository.encounter.search import revinclude_encounters_via_child

        return await revinclude_encounters_via_child(
            EncounterParticipant, resource_type, key
        )(session, ctx, rows)

    return tuple(
        IncludeTarget("Encounter", param, resource_type, fetch, reverse=True)
        for param in params
    )


def location_encounter_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Encounter:location — encounters held at one of the matched Locations."""

    async def fetch(session, ctx, rows):
        from app.models.encounter import EncounterLocation
        from app.repository.encounter.search import revinclude_encounters_via_child

        return await revinclude_encounters_via_child(
            EncounterLocation, "Location", key
        )(session, ctx, rows)

    return (IncludeTarget("Encounter", "location", "Location", fetch, reverse=True),)


def appointment_encounter_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Encounter:appointment — encounters that came out of one of the matched
    Appointments."""

    async def fetch(session, ctx, rows):
        from app.repository.encounter.search import (
            revinclude_encounters_via_appointment,
        )

        return await revinclude_encounters_via_appointment(key)(session, ctx, rows)

    return (
        IncludeTarget("Encounter", "appointment", "Appointment", fetch, reverse=True),
    )


def service_provider_encounter_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Encounter:service-provider — encounters an Organization is responsible for."""

    async def fetch(session, ctx, rows):
        from app.repository.encounter.search import revinclude_encounters_via_column

        return await revinclude_encounters_via_column(
            "service_provider", "Organization", key
        )(session, ctx, rows)

    return (
        IncludeTarget(
            "Encounter", "service-provider", "Organization", fetch, reverse=True
        ),
    )


def reference_encounter_revincludes(
    resource_type: str, key, params: tuple[str, ...] = ("diagnosis", "reason-reference")
) -> tuple[IncludeTarget, ...]:
    """Encounter:diagnosis and :reason-reference — encounters whose diagnosis /
    reason points at one of the matched rows of `resource_type` (Condition or
    Procedure; an Observation can only be a reason, so it passes
    `params=("reason-reference",)`)."""

    def make(param: str):
        async def fetch(session, ctx, rows):
            from app.repository.encounter.search import (
                revinclude_encounters_via_reference,
            )

            return await revinclude_encounters_via_reference(param, resource_type, key)(
                session, ctx, rows
            )

        return fetch

    return tuple(
        IncludeTarget("Encounter", param, resource_type, make(param), reverse=True)
        for param in params
    )
