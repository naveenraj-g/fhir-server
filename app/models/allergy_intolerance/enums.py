from enum import Enum


class AllergyIntoleranceType(str, Enum):
    allergy = "allergy"
    intolerance = "intolerance"


class AllergyIntoleranceCategory(str, Enum):
    food = "food"
    medication = "medication"
    environment = "environment"
    biologic = "biologic"


class AllergyIntoleranceCriticality(str, Enum):
    low = "low"
    high = "high"
    unable_to_assess = "unable-to-assess"


class AllergyIntoleranceSeverity(str, Enum):
    mild = "mild"
    moderate = "moderate"
    severe = "severe"


class AllergyIntolerancePatientReferenceType(str, Enum):
    Patient = "Patient"


class AllergyIntoleranceEncounterReferenceType(str, Enum):
    Encounter = "Encounter"


class AllergyIntoleranceRecorderReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"


class AllergyIntoleranceAsserterReferenceType(str, Enum):
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class AllergyIntoleranceNoteAuthorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
