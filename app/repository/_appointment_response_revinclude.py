"""`_revinclude=AppointmentResponse:...` declarations for the registries of the
resources an AppointmentResponse points at (Appointment, Patient, Practitioner,
PractitionerRole, HealthcareService, Location).

Kept in one neutral module that imports the AppointmentResponse registry
lazily, so the registries don't import each other at load (same arrangement as
`_appointment_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def actor_response_revincludes(resource_type: str, key, params: tuple[str, ...]) -> tuple[IncludeTarget, ...]:
    """AppointmentResponse:<param> for each of `params` (`actor`, and the
    narrowed `patient` / `practitioner` / `location`) — responses whose actor
    is of `resource_type` and points at one of the matched rows (matched on the
    public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        from app.repository.appointment_response.search import revinclude_responses_via_actor

        return await revinclude_responses_via_actor(resource_type, key)(session, ctx, rows)

    return tuple(IncludeTarget("AppointmentResponse", param, resource_type, fetch, reverse=True) for param in params)


def appointment_response_revincludes(key) -> tuple[IncludeTarget, ...]:
    """AppointmentResponse:appointment — responses replying to one of the
    matched appointments."""

    async def fetch(session, ctx, rows):
        from app.repository.appointment_response.search import revinclude_responses_via_appointment

        return await revinclude_responses_via_appointment(key)(session, ctx, rows)

    return (IncludeTarget("AppointmentResponse", "appointment", "Appointment", fetch, reverse=True),)
