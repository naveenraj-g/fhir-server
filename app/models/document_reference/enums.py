from enum import Enum


class DocumentReferenceStatus(str, Enum):
    """FHIR DocumentReference.status value set (code, required) —
    https://www.hl7.org/fhir/R4/valueset-document-reference-status.html
    """

    current = "current"
    superseded = "superseded"
    entered_in_error = "entered-in-error"


class DocumentReferenceDocStatus(str, Enum):
    """FHIR DocumentReference.docStatus value set (code, required) —
    http://hl7.org/fhir/composition-status
    """

    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    entered_in_error = "entered-in-error"


class DocumentRelationshipType(str, Enum):
    """FHIR DocumentReference.relatesTo.code value set (code, required) —
    http://hl7.org/fhir/document-relationship-type
    """

    replaces = "replaces"
    transforms = "transforms"
    signs = "signs"
    appends = "appends"


class DocumentReferenceSubjectReferenceType(str, Enum):
    """DocumentReference.subject Reference(Patient | Practitioner | Group | Device)."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    Group = "Group"
    Device = "Device"


class DocumentReferenceAuthorReferenceType(str, Enum):
    """DocumentReference.author Reference(Practitioner | PractitionerRole | Organization | Device | Patient | RelatedPerson)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Device = "Device"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"


class DocumentReferenceAuthenticatorReferenceType(str, Enum):
    """DocumentReference.authenticator Reference(Practitioner | PractitionerRole | Organization)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"


class DocumentReferenceTargetReferenceType(str, Enum):
    """DocumentReference.relatesTo.target Reference(DocumentReference)."""

    DocumentReference = "DocumentReference"


class DocumentReferenceContextEncounterReferenceType(str, Enum):
    """DocumentReference.context.encounter Reference(Encounter | EpisodeOfCare)."""

    Encounter = "Encounter"
    EpisodeOfCare = "EpisodeOfCare"


class DocumentReferencePatientReferenceType(str, Enum):
    """DocumentReference.context.sourcePatientInfo Reference(Patient)."""

    Patient = "Patient"
