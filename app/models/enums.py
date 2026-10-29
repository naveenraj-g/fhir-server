from enum import Enum


class SubjectReferenceType(str, Enum):
    """Shared subject reference types used across Encounter, Appointment, QuestionnaireResponse.
    All three store this as DB type name 'subject_reference_type'."""

    Patient = "Patient"
    Group = "Group"


class OrganizationReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is Organization.
    Stored as DB type name 'organization_reference_type' (shared across all tables).
    NOTE: this is a FHIR resource reference — distinct from the tenant org_id column."""

    Organization = "Organization"


class EncounterReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is Encounter.
    Stored as DB type name 'encounter_reference_type' (shared across all tables, create_type=False)."""

    Encounter = "Encounter"


class PractitionerReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is Practitioner.
    Stored as DB type name 'practitioner_reference_type' (shared across all tables,
    create_type=False once PractitionerRole's migration creates it)."""

    Practitioner = "Practitioner"


class ScheduleReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is Schedule.
    Stored as DB type name 'schedule_reference_type' (shared across all tables,
    create_type=False once Slot's migration creates it)."""

    Schedule = "Schedule"


class AppointmentReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is Appointment.
    Stored as DB type name 'appointment_reference_type' (shared across all tables,
    create_type=False once AppointmentResponse's migration creates it)."""

    Appointment = "Appointment"


class LocationReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is Location.
    Stored as DB type name 'location_reference_type' (shared across all tables,
    create_type=False once a later migration creates it)."""

    Location = "Location"


class ServiceRequestReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is
    ServiceRequest (e.g. ServiceRequest.replaces, and the ServiceRequest
    member of ServiceRequest.basedOn's own 3-member enum). Stored as DB
    type name 'service_request_reference_type' (shared across all tables,
    create_type=False once a later migration creates it)."""

    ServiceRequest = "ServiceRequest"


class MedicationRequestReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is
    MedicationRequest (e.g. MedicationRequest.priorPrescription). Stored
    as DB type name 'medication_request_reference_type' (shared across
    all tables, create_type=False once a later migration creates it)."""

    MedicationRequest = "MedicationRequest"


class IdentifierUse(str, Enum):
    """FHIR R4 IdentifierUse — used by any resource that stores an identifier.use column."""

    usual = "usual"
    official = "official"
    temp = "temp"
    secondary = "secondary"
    old = "old"
