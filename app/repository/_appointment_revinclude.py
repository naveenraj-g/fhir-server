"""`_revinclude=Appointment:...` declarations for the registries of the
resources an Appointment points at (Patient, Practitioner, PractitionerRole,
HealthcareService, Location, Slot).

Kept in one neutral module that imports the Appointment registry lazily, so the
registries don't import each other at load (same arrangement as the
`_revinclude_patients` helpers)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def participant_revincludes(resource_type: str, key, params: tuple[str, ...]) -> tuple[IncludeTarget, ...]:
    """Appointment:<param> for each of `params` (`actor`, and the narrowed
    `patient` / `practitioner` / `location`) — appointments with a participant
    actor of `resource_type` pointing at one of the matched rows (matched on the
    public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        from app.repository.appointment.search import revinclude_appointments_via_participant

        return await revinclude_appointments_via_participant(resource_type, key)(session, ctx, rows)

    return tuple(IncludeTarget("Appointment", param, resource_type, fetch, reverse=True) for param in params)


def slot_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Appointment:slot — appointments that fill one of the matched slots."""

    async def fetch(session, ctx, rows):
        from app.repository.appointment.search import revinclude_appointments_via_slot

        return await revinclude_appointments_via_slot(key)(session, ctx, rows)

    return (IncludeTarget("Appointment", "slot", "Slot", fetch, reverse=True),)


def condition_appointment_revincludes(key) -> tuple[IncludeTarget, ...]:
    """Appointment:reason-reference — appointments whose reason is one of the
    matched Conditions."""

    async def fetch(session, ctx, rows):
        from app.repository.appointment.search import revinclude_appointments_via_condition

        return await revinclude_appointments_via_condition(key)(session, ctx, rows)

    return (IncludeTarget("Appointment", "reason-reference", "Condition", fetch, reverse=True),)
