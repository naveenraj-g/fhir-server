from enum import Enum


class ProcedureStatus(str, Enum):
    """Procedure event-status: preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown."""

    preparation = "preparation"
    in_progress = "in-progress"
    not_done = "not-done"
    on_hold = "on-hold"
    stopped = "stopped"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class ProcedureSubjectReferenceType(str, Enum):
    """Procedure.subject allowed target types in R4."""

    Patient = "Patient"
    Group = "Group"


class ProcedureBasedOnReferenceType(str, Enum):
    """Procedure.basedOn allowed target types in R4."""

    CarePlan = "CarePlan"
    ServiceRequest = "ServiceRequest"


class ProcedurePartOfReferenceType(str, Enum):
    """Procedure.partOf allowed target types in R4."""

    Procedure = "Procedure"
    Observation = "Observation"
    MedicationAdministration = "MedicationAdministration"


class ProcedureRecorderReferenceType(str, Enum):
    """Procedure.recorder allowed target types in R4."""

    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class ProcedureAsserterReferenceType(str, Enum):
    """Procedure.asserter allowed target types in R4."""

    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class ProcedurePerformerActorReferenceType(str, Enum):
    """Procedure.performer.actor allowed target types in R4."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Device = "Device"


class ProcedureReasonReferenceReferenceType(str, Enum):
    """Procedure.reasonReference allowed target types in R4."""

    Condition = "Condition"
    Observation = "Observation"
    Procedure = "Procedure"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"


class ProcedureReportReferenceType(str, Enum):
    """Procedure.report allowed target types in R4."""

    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"
    Composition = "Composition"


class ProcedureComplicationDetailReferenceType(str, Enum):
    """Procedure.complicationDetail allowed target types in R4."""

    Condition = "Condition"


class ProcedureFocalDeviceManipulatedReferenceType(str, Enum):
    """Procedure.focalDevice.manipulated allowed target types in R4."""

    Device = "Device"


class ProcedureUsedReferenceReferenceType(str, Enum):
    """Procedure.usedReference allowed target types in R4."""

    Device = "Device"
    Medication = "Medication"
    Substance = "Substance"


class ProcedureAuthorReferenceType(str, Enum):
    """Annotation.authorReference allowed target types in R4."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"

