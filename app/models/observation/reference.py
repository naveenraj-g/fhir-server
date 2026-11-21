from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The reference parameters held in ObservationReference, and the element each reads.
REFERENCE_PARAMS = {
    "based-on": "basedOn",
    "part-of": "partOf",
    "focus": "focus",
    "has-member": "hasMember",
    "derived-from": "derivedFrom",
    "performer": "performer",
}
# R4 targets of each parameter.
BASED_ON_TYPES = (
    "CarePlan", "DeviceRequest", "ImmunizationRecommendation", "MedicationRequest", "NutritionOrder",
    "ServiceRequest",
)
PART_OF_TYPES = (
    "MedicationAdministration", "MedicationDispense", "MedicationStatement", "Procedure", "Immunization",
    "ImagingStudy",
)
PERFORMER_TYPES = ("Practitioner", "PractitionerRole", "Organization", "CareTeam", "Patient", "RelatedPerson")
HAS_MEMBER_TYPES = ("Observation", "QuestionnaireResponse", "MolecularSequence")
DERIVED_FROM_TYPES = (
    "DocumentReference", "ImagingStudy", "Media", "QuestionnaireResponse", "Observation", "MolecularSequence",
)
# `focus` is Reference(Any): the parser only accepts `:Type` for a declared target, so list the
# types an Observation can realistically focus on. A relative reference to a type not listed is
# still indexed (and found by its absolute URL).
FOCUS_TYPES = (
    "Patient", "Practitioner", "PractitionerRole", "RelatedPerson", "Organization", "Location",
    "HealthcareService", "Encounter", "Appointment", "Condition", "Observation", "Procedure",
    "DiagnosticReport", "DocumentReference", "ServiceRequest", "MedicationRequest", "MedicationStatement",
    "MedicationAdministration", "MedicationDispense", "CarePlan", "AllergyIntolerance", "Immunization",
    "FamilyMemberHistory", "RiskAssessment", "ClinicalImpression", "DetectedIssue", "Specimen", "Device",
)
REFERENCE_TYPES = {
    "based-on": BASED_ON_TYPES,
    "part-of": PART_OF_TYPES,
    "focus": FOCUS_TYPES,
    "has-member": HAS_MEMBER_TYPES,
    "derived-from": DERIVED_FROM_TYPES,
    "performer": PERFORMER_TYPES,
}


class ObservationReference(Base):
    """Search index for the six repeating reference parameters `based-on`, `part-of`, `focus`,
    `has-member`, `derived-from` and `performer`: one row per Reference that has a `reference` or
    an `identifier` (one with only `display` cannot be matched by a reference search). `param` says
    which parameter the row belongs to (see REFERENCE_PARAMS). Derived from ObservationModel.content
    — never read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain string, not a
    Postgres enum (every one of these can point at several types, and `focus` at any type; a
    search by bare id is ambiguous).

      <param>             -> reference_type/reference_id or reference_reference
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` and no UniqueConstraint: R4 does not forbid listing the same
    reference twice."""

    __tablename__ = "observation_reference"
    __table_args__ = (Index("ix_observation_reference_param_type_id", "param", "reference_type", "reference_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    observation = relationship("ObservationModel", back_populates="references")
