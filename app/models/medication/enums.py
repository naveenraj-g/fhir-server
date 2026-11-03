from enum import Enum


class MedicationStatus(str, Enum):
    """Medication.status (0..1 code) —
    http://hl7.org/fhir/R4/valueset-medication-status.html
    """

    active = "active"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


class MedicationManufacturerReferenceType(str, Enum):
    """Medication.manufacturer Reference(Organization)."""

    Organization = "Organization"


class MedicationIngredientItemReferenceType(str, Enum):
    """Medication.ingredient.item Reference(Substance | Medication)."""

    Substance = "Substance"
    Medication = "Medication"


class MedicationIdentifierAssignerReferenceType(str, Enum):
    """Medication.identifier.assigner Reference(Organization)."""

    Organization = "Organization"


class MedicationQuantityComparator(str, Enum):
    """Medication ratio numerator/denominator Quantity comparator."""

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"
