from enum import Enum


class AppointmentStatus(str, Enum):
    proposed = "proposed"
    pending = "pending"
    booked = "booked"
    arrived = "arrived"
    fulfilled = "fulfilled"
    cancelled = "cancelled"
    noshow = "noshow"
    entered_in_error = "entered-in-error"
    checked_in = "checked-in"
    waitlist = "waitlist"


class AppointmentParticipantStatus(str, Enum):
    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"
    needs_action = "needs-action"


class AppointmentParticipantRequired(str, Enum):
    """FHIR R4 Appointment.participant.required value set."""

    required = "required"
    optional = "optional"
    information_only = "information-only"


class AppointmentParticipantActorType(str, Enum):
    """FHIR R4 reference types for Appointment.participant.actor."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Device = "Device"
    HealthcareService = "HealthcareService"
    Location = "Location"


class AppointmentReasonReferenceType(str, Enum):
    """Allowed reference types for Appointment.reasonReference."""

    Condition = "Condition"
    Procedure = "Procedure"
    Observation = "Observation"
    ImmunizationRecommendation = "ImmunizationRecommendation"


class AppointmentSlotReferenceType(str, Enum):
    """Allowed reference types for Appointment.slot[]."""

    Slot = "Slot"


class AppointmentBasedOnReferenceType(str, Enum):
    """Allowed reference types for Appointment.basedOn (Reference(ServiceRequest))."""

    ServiceRequest = "ServiceRequest"
