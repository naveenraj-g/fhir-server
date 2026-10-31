from enum import Enum


class RelatedPersonPatientReferenceType(str, Enum):
    """Allowed reference types for RelatedPerson.patient (1..1 Reference(Patient))."""

    Patient = "Patient"
