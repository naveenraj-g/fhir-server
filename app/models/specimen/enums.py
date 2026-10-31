from enum import Enum


class SpecimenStatus(str, Enum):
    """FHIR Specimen.status value set (code, required) —
    https://www.hl7.org/fhir/R4/valueset-specimen-status.html
    """

    available = "available"
    unavailable = "unavailable"
    unsatisfactory = "unsatisfactory"
    entered_in_error = "entered-in-error"


class SpecimenQuantityComparator(str, Enum):
    """Bound to SpecimenQuantityComparator in app.schemas.enums.
    Model-layer values are alphanumeric identifiers; schema-layer values are FHIR symbols.
    """

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"


class SpecimenSubjectReferenceType(str, Enum):
    """Specimen.subject Reference(Patient | Group | Device | Substance | Location)."""

    Patient = "Patient"
    Group = "Group"
    Device = "Device"
    Substance = "Substance"
    Location = "Location"


class SpecimenCollectorReferenceType(str, Enum):
    """Specimen.collection.collector Reference(Practitioner | PractitionerRole)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class SpecimenParentReferenceType(str, Enum):
    """Specimen.parent Reference(Specimen)."""

    Specimen = "Specimen"


class SpecimenAdditiveReferenceType(str, Enum):
    """Specimen.processing.additive and container.additiveReference Reference(Substance)."""

    Substance = "Substance"


class SpecimenNoteAuthorReferenceType(str, Enum):
    """Specimen.note.author Reference(Practitioner | PractitionerRole | Patient | RelatedPerson)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
