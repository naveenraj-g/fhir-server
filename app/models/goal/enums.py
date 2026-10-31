from enum import Enum


class GoalLifecycleStatus(str, Enum):
    """FHIR R4 GoalLifecycleStatus value set (required binding).
    https://www.hl7.org/fhir/R4/valueset-goal-status.html
    """

    proposed = "proposed"
    planned = "planned"
    accepted = "accepted"
    active = "active"
    on_hold = "on-hold"
    completed = "completed"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    rejected = "rejected"


class GoalSubjectReferenceType(str, Enum):
    """Allowed reference types for Goal.subject (Patient|Group|Organization)."""

    Patient = "Patient"
    Group = "Group"
    Organization = "Organization"


class GoalExpressedByReferenceType(str, Enum):
    """Allowed reference types for Goal.expressedBy (Patient|Practitioner|PractitionerRole|RelatedPerson)."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"


class GoalAddressesReferenceType(str, Enum):
    """Allowed reference types for Goal.addresses (Condition|Observation|MedicationStatement|NutritionOrder|ServiceRequest|RiskAssessment)."""

    Condition = "Condition"
    Observation = "Observation"
    MedicationStatement = "MedicationStatement"
    NutritionOrder = "NutritionOrder"
    ServiceRequest = "ServiceRequest"
    RiskAssessment = "RiskAssessment"


class GoalOutcomeReferenceType(str, Enum):
    """Allowed reference types for Goal.outcomeReference (Observation)."""

    Observation = "Observation"
