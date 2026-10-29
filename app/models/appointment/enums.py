from enum import Enum


class AppointmentStatus(str, Enum):
    """FHIR R4 Appointment.status (1..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-appointmentstatus.html

    Member name intentionally equals member value (both underscore-only,
    not the true hyphenated FHIR code) — see CLAUDE.md's FHIR DB Model
    Design "Alembic autogenerate enum values are correct (key = value
    convention)" invariant and app.models.slot.enums.SlotStatus's docstring
    for the full reasoning: SQLAlchemy's `Enum(PyEnum)` stores each member's
    `.name` in Postgres by default, so the real `entered-in-error`/
    `checked-in` FHIR codes are rendered explicitly in
    app/fhir/mappers/appointment/fhir.py instead of fighting that default
    with `values_callable`.
    """

    proposed = "proposed"
    pending = "pending"
    booked = "booked"
    arrived = "arrived"
    fulfilled = "fulfilled"
    cancelled = "cancelled"
    noshow = "noshow"
    entered_in_error = "entered_in_error"
    checked_in = "checked_in"
    waitlist = "waitlist"


class AppointmentParticipantRequired(str, Enum):
    """FHIR R4 Appointment.participant.required (0..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-participantrequired.html
    Member name == member value, underscore-only — see AppointmentStatus's
    docstring (`information-only`'s real hyphenated code is rendered in the
    mapper).
    """

    required = "required"
    optional = "optional"
    information_only = "information_only"


class AppointmentParticipationStatus(str, Enum):
    """FHIR R4 Appointment.participant.status (1..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-participationstatus.html
    Member name == member value, underscore-only — see AppointmentStatus's
    docstring (`needs-action`'s real hyphenated code is rendered in the
    mapper).
    """

    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"
    needs_action = "needs_action"


class AppointmentParticipantActorReferenceType(str, Enum):
    """Allowed reference types for Appointment.participant.actor (0..1).
    FHIR R4 allows Patient|Practitioner|PractitionerRole|RelatedPerson|
    Device|HealthcareService|Location as the target — of these, only
    Practitioner, PractitionerRole, HealthcareService, and Location are
    modeled resources in this system (registered in RESOURCE_REGISTRY, see
    app/core/reference_resolver.py); Patient, RelatedPerson, and Device rows
    will in practice always rely on the reference_identifier_* logical-
    reference fallback instead of a resolved reference_id — same situation
    and same reasoning as app.models.schedule.enums.ScheduleActorReferenceType,
    kept as its own separate enum/DB type rather than reused across
    resources (not one of the globally shared types in app/models/enums.py).
    """

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Device = "Device"
    HealthcareService = "HealthcareService"
    Location = "Location"


class AppointmentReasonReferenceType(str, Enum):
    """Allowed reference types for Appointment.reasonReference[] (0..*).
    FHIR R4 allows Condition|Procedure|Observation|ImmunizationRecommendation
    as the target — none of these are modeled resources in this system, so
    every row relies on the reference_identifier_* logical-reference
    fallback (or just the raw reference_reference string) instead of a
    resolved reference_id; the existence check is never attempted for this
    field at all (see app.repository.appointment._shared's docstring),
    same situation as HealthcareServiceEndpoint (Endpoint isn't modeled
    either).
    """

    Condition = "Condition"
    Procedure = "Procedure"
    Observation = "Observation"
    ImmunizationRecommendation = "ImmunizationRecommendation"


class AppointmentSlotReferenceType(str, Enum):
    """Allowed reference type for Appointment.slot[] (0..*) — a Slot is the
    only allowed target. Slot IS a modeled resource in this system
    (registered in RESOURCE_REGISTRY once this build registers it), so this
    reference's existence check is actually enforced, unlike reasonReference/
    basedOn/supportingInformation above/below."""

    Slot = "Slot"


class AppointmentBasedOnReferenceType(str, Enum):
    """Allowed reference type for Appointment.basedOn[] (0..*) — a
    ServiceRequest is the only allowed target. ServiceRequest is not a
    modeled resource in this system, so this reference's existence check is
    never attempted — same situation as AppointmentReasonReferenceType."""

    ServiceRequest = "ServiceRequest"
