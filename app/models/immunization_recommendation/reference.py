from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The two reference parameters held in ImmunizationRecommendationReference, and the
# element each reads.
REFERENCE_PARAMS = {
    "support": "recommendation.supportingImmunization",
    "information": "recommendation.supportingPatientInformation",
}
# R4 targets of `support`.
SUPPORT_TYPES = ("Immunization", "ImmunizationEvaluation")
# `information` is Reference(Any): the parser only accepts `:Type` for a declared
# target, so list the types a piece of patient information can realistically be. A
# relative reference to a type not listed is still indexed (and found by its
# absolute URL).
INFORMATION_TYPES = (
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Organization",
    "Location",
    "Encounter",
    "Appointment",
    "Condition",
    "Observation",
    "Procedure",
    "DiagnosticReport",
    "DocumentReference",
    "ServiceRequest",
    "MedicationRequest",
    "MedicationStatement",
    "MedicationDispense",
    "MedicationAdministration",
    "CarePlan",
    "AllergyIntolerance",
    "Immunization",
    "FamilyMemberHistory",
    "Questionnaire",
    "QuestionnaireResponse",
)
REFERENCE_TYPES = {"support": SUPPORT_TYPES, "information": INFORMATION_TYPES}


class ImmunizationRecommendationReference(Base):
    """Search index for the two repeating reference parameters `support`
    (recommendation.supportingImmunization) and `information`
    (recommendation.supportingPatientInformation): one row per Reference that has a
    `reference` or an `identifier` (one with only `display` cannot be matched by a
    reference search). `param` says which parameter the row belongs to. Derived from
    ImmunizationRecommendationModel.content — never read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain
    string, not a Postgres enum (both elements can point at several types, and
    `information` at any type; a search by bare id is ambiguous).

      <param>             -> reference_type/reference_id or reference_reference
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` and no UniqueConstraint: R4 does not forbid
    listing the same reference twice."""

    __tablename__ = "immunization_recommendation_reference"
    __table_args__ = (
        Index(
            "ix_immunization_recommendation_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_recommendation_pk = Column(
        BigInteger,
        ForeignKey("immunization_recommendation.id"),
        nullable=False,
        index=True,
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    immunization_recommendation = relationship(
        "ImmunizationRecommendationModel", back_populates="references"
    )
