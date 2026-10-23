from enum import Enum


class ScheduleActorReferenceType(str, Enum):
    """Allowed reference types for Schedule.actor[] (1..* per FHIR R4, though
    not enforced at the DB layer — see app/fhir-db-model's "no DB-level CHECK
    constraints" convention). FHIR R4 allows Patient|Practitioner|
    PractitionerRole|RelatedPerson|Device|HealthcareService|Location as the
    target — of these, only Practitioner, PractitionerRole, HealthcareService,
    and Location are modeled resources in this system (registered in
    RESOURCE_REGISTRY); Patient, RelatedPerson, and Device rows will in
    practice always rely on the reference_identifier_* logical-reference
    fallback instead of a resolved reference_id.
    """

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Device = "Device"
    HealthcareService = "HealthcareService"
    Location = "Location"
