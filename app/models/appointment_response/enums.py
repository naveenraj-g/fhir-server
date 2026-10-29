from enum import Enum


class AppointmentResponseParticipantStatus(str, Enum):
    """FHIR R4 AppointmentResponse.participantStatus (1..1, required
    binding) — https://www.hl7.org/fhir/R4/valueset-participationstatus.html

    Same value set as app.models.appointment.enums.AppointmentParticipationStatus
    (Appointment.participant.status) — kept as its own separate enum/DB
    type rather than reused across resources, consistent with this
    codebase's convention (e.g. HealthcareServiceDayOfWeek vs
    PractitionerRoleDayOfWeek at the Pydantic layer: identical value sets,
    still one enum class per resource+field).

    Member name intentionally equals member value (both underscore-only,
    not the true hyphenated FHIR code) — see
    app.models.slot.enums.SlotStatus's docstring for the full reasoning:
    SQLAlchemy's `Enum(PyEnum)` stores each member's `.name` in Postgres by
    default, so the real `needs-action` FHIR code is rendered explicitly
    in app/fhir/mappers/appointment_response/fhir.py instead.
    """

    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"
    needs_action = "needs_action"


class AppointmentResponseActorReferenceType(str, Enum):
    """Allowed reference types for AppointmentResponse.actor (0..1).
    FHIR R4 allows Patient|Practitioner|PractitionerRole|RelatedPerson|
    Device|HealthcareService|Location as the target — of these, only
    Practitioner, PractitionerRole, HealthcareService, and Location are
    modeled resources in this system (registered in RESOURCE_REGISTRY, see
    app/core/reference_resolver.py); Patient, RelatedPerson, and Device
    rows will in practice always rely on the reference_identifier_*
    logical-reference fallback instead of a resolved reference_id — same
    situation as app.models.appointment.enums.AppointmentParticipantActorReferenceType,
    kept as its own separate enum/DB type rather than reused across
    resources.
    """

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Device = "Device"
    HealthcareService = "HealthcareService"
    Location = "Location"
