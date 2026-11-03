from enum import Enum


class MedicationKnowledgeStatus(str, Enum):
    """FHIR MedicationKnowledge.status value set (code) —
    http://hl7.org/fhir/R4/valueset-medicationknowledge-status.html
    """

    active = "active"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


class MedicationKnowledgeManufacturerReferenceType(str, Enum):
    Organization = "Organization"


class MedicationKnowledgeRelatedReferenceType(str, Enum):
    MedicationKnowledge = "MedicationKnowledge"


class MedicationKnowledgeAssociatedMedicationReferenceType(str, Enum):
    Medication = "Medication"


class MedicationKnowledgeMonographSourceReferenceType(str, Enum):
    DocumentReference = "DocumentReference"
    Media = "Media"


class MedicationKnowledgeIngredientItemReferenceType(str, Enum):
    Substance = "Substance"
    Medication = "Medication"


class MedicationKnowledgeAdminGuidelineIndicationReferenceType(str, Enum):
    ObservationDefinition = "ObservationDefinition"


class MedicationKnowledgeContraindicationReferenceType(str, Enum):
    DetectedIssue = "DetectedIssue"


class MedicationKnowledgeRegulatoryAuthorityReferenceType(str, Enum):
    Organization = "Organization"


class MedicationKnowledgeQuantityComparator(str, Enum):
    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"
