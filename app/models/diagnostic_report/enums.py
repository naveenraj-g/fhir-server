from enum import Enum

# ---------------------------------------------------------------------------
# Status enum — key always equals value. Hyphenated FHIR codes
# (entered-in-error) can't be a Python identifier, so both the model-layer
# and schema-layer enums use the underscored spelling for the NAME; only
# the schema-layer enum's VALUE carries the real hyphenated wire code. The
# model-layer value stays underscored too (what's actually stored in the
# Postgres enum type) — conversion between the two always goes by member
# NAME (see CLAUDE.md's "Converting a Pydantic schema enum's .value..."
# rule), never by value.
# ---------------------------------------------------------------------------


class DiagnosticReportStatus(str, Enum):
    registered = "registered"
    partial = "partial"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    appended = "appended"
    cancelled = "cancelled"
    entered_in_error = "entered_in_error"
    unknown = "unknown"


# ---------------------------------------------------------------------------
# Reference-type enums — local to DiagnosticReport (multi-member, or
# single-member for a target that isn't a modeled resource in this system
# yet). A single-member enum for a MODELED target (Observation.result)
# lives in the shared app/models/enums.py instead — see
# ObservationReferenceType there.
# ---------------------------------------------------------------------------


class DiagnosticReportBasedOnReferenceType(str, Enum):
    """basedOn — Reference(CarePlan|ImmunizationRecommendation|
    MedicationRequest|NutritionOrder|ServiceRequest). MedicationRequest,
    ServiceRequest, and CarePlan are modeled resources in this system
    today — note CarePlan is NOT modeled either (name only reserved in
    CLAUDE.md's sequence table), so only MedicationRequest/ServiceRequest
    are actually checked for existence."""

    CarePlan = "CarePlan"
    ImmunizationRecommendation = "ImmunizationRecommendation"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    ServiceRequest = "ServiceRequest"


class DiagnosticReportSubjectReferenceType(str, Enum):
    """subject — Reference(Patient|Group|Device|Location). Only Location
    is a modeled resource in this system today."""

    Patient = "Patient"
    Group = "Group"
    Device = "Device"
    Location = "Location"


class DiagnosticReportActorReferenceType(str, Enum):
    """Shared by both performer and resultsInterpreter — Reference(
    Practitioner|PractitionerRole|Organization|CareTeam), the identical
    4-member set on both fields per spec. Practitioner/PractitionerRole/
    Organization are the only modeled resources among these today. One
    Python enum class backs both columns' Postgres type (performer_type
    creates it; results_interpreter_type reuses it with create_type=False),
    same pattern as any other type shared across tables/columns."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    CareTeam = "CareTeam"


class DiagnosticReportSpecimenReferenceType(str, Enum):
    """specimen — Reference(Specimen). Specimen is not a modeled resource
    in this system today — the existence check is never attempted."""

    Specimen = "Specimen"


class DiagnosticReportImagingStudyReferenceType(str, Enum):
    """imagingStudy — Reference(ImagingStudy). ImagingStudy is not a
    modeled resource in this system today."""

    ImagingStudy = "ImagingStudy"


class DiagnosticReportMediaLinkReferenceType(str, Enum):
    """media.link — Reference(Media). Media is not a modeled resource in
    this system today."""

    Media = "Media"
