from enum import Enum

# ---------------------------------------------------------------------------
# Status / code enums — key always equals value. Hyphenated FHIR codes
# (entered-in-error) can't be a Python identifier, so both the model-layer
# and schema-layer enums use the underscored spelling for the NAME; only
# the schema-layer enum's VALUE carries the real hyphenated wire code. The
# model-layer value stays underscored too (what's actually stored in the
# Postgres enum type) — conversion between the two always goes by member
# NAME (see CLAUDE.md's "Converting a Pydantic schema enum's .value..."
# rule), never by value.
# ---------------------------------------------------------------------------


class ObservationStatus(str, Enum):
    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered_in_error"
    unknown = "unknown"


class ObservationQuantityComparator(str, Enum):
    """Bound to QuantityComparator — used by value_quantity.comparator and
    value_ratio's numerator/denominator.comparator (both plain Quantity,
    unlike Range/SampledData's SimpleQuantity, which forbids comparator
    entirely and so has no column for it at all)."""

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"


# ---------------------------------------------------------------------------
# Reference-type enums — local to Observation (multi-member, or single-
# member for a target that isn't a modeled resource in this system yet).
# ---------------------------------------------------------------------------


class ObservationSubjectReferenceType(str, Enum):
    """subject — Reference(Patient|Group|Device|Location). Only Location
    is a modeled resource in this system today."""

    Patient = "Patient"
    Group = "Group"
    Device = "Device"
    Location = "Location"


class ObservationBasedOnReferenceType(str, Enum):
    """basedOn — Reference(CarePlan|DeviceRequest|ImmunizationRecommendation|
    MedicationRequest|NutritionOrder|ServiceRequest). MedicationRequest and
    ServiceRequest are the only modeled resources among these today."""

    CarePlan = "CarePlan"
    DeviceRequest = "DeviceRequest"
    ImmunizationRecommendation = "ImmunizationRecommendation"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    ServiceRequest = "ServiceRequest"


class ObservationPartOfReferenceType(str, Enum):
    """partOf — Reference(MedicationAdministration|MedicationDispense|
    MedicationStatement|Procedure|Immunization|ImagingStudy). None of
    these is a modeled resource in this system today — the existence
    check is never attempted for this field."""

    MedicationAdministration = "MedicationAdministration"
    MedicationDispense = "MedicationDispense"
    MedicationStatement = "MedicationStatement"
    Procedure = "Procedure"
    Immunization = "Immunization"
    ImagingStudy = "ImagingStudy"


class ObservationPerformerReferenceType(str, Enum):
    """performer — Reference(Practitioner|PractitionerRole|Organization|
    CareTeam|Patient|RelatedPerson). Practitioner/PractitionerRole/
    Organization are the only modeled resources among these today."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    CareTeam = "CareTeam"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"


class ObservationSpecimenReferenceType(str, Enum):
    """specimen — Reference(Specimen). Specimen is not a modeled resource
    in this system today — the existence check is never attempted."""

    Specimen = "Specimen"


class ObservationDeviceReferenceType(str, Enum):
    """device — Reference(Device|DeviceMetric). Neither is a modeled
    resource in this system today."""

    Device = "Device"
    DeviceMetric = "DeviceMetric"


class ObservationHasMemberReferenceType(str, Enum):
    """hasMember — Reference(Observation|QuestionnaireResponse|
    MolecularSequence). Observation (self-referential) and
    QuestionnaireResponse are the only modeled resources among these."""

    Observation = "Observation"
    QuestionnaireResponse = "QuestionnaireResponse"
    MolecularSequence = "MolecularSequence"


class ObservationDerivedFromReferenceType(str, Enum):
    """derivedFrom — Reference(DocumentReference|ImagingStudy|Media|
    QuestionnaireResponse|Observation|MolecularSequence). Observation
    (self-referential) and QuestionnaireResponse are the only modeled
    resources among these."""

    DocumentReference = "DocumentReference"
    ImagingStudy = "ImagingStudy"
    Media = "Media"
    QuestionnaireResponse = "QuestionnaireResponse"
    Observation = "Observation"
    MolecularSequence = "MolecularSequence"


class ObservationNoteAuthorReferenceType(str, Enum):
    """note.authorReference — Annotation.author[x]'s Reference variant is
    Reference(Practitioner|PractitionerRole|Patient|RelatedPerson|
    Organization) per the base Annotation datatype (not resource-
    specific). Practitioner/PractitionerRole/Organization are the only
    modeled resources among these."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"
