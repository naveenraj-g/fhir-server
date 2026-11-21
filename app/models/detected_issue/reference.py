from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The reference parameter held in DetectedIssueReference, and the element it reads.
REFERENCE_PARAMS = {
    "implicated": "implicated",
}
# `implicated` is Reference(Any): the parser only accepts `:Type` for a declared target, so
# list the types an implicated resource can realistically be. A relative reference to a type
# not listed is still indexed (and found by its absolute URL).
IMPLICATED_TYPES = (
    "Patient", "Practitioner", "PractitionerRole", "RelatedPerson", "Organization", "Location",
    "HealthcareService", "Encounter", "Appointment", "Condition", "Observation", "Procedure",
    "DiagnosticReport", "DocumentReference", "ServiceRequest", "MedicationRequest",
    "MedicationStatement", "MedicationAdministration", "MedicationDispense", "CarePlan",
    "AllergyIntolerance", "Immunization", "FamilyMemberHistory", "RiskAssessment", "ClinicalImpression",
    "Device",
)
REFERENCE_TYPES = {"implicated": IMPLICATED_TYPES}


class DetectedIssueReference(Base):
    """Search index for the repeating reference parameter `implicated`: one row per Reference
    that has a `reference` or an `identifier` (one with only `display` cannot be matched by a
    reference search). `param` says which parameter the row belongs to (see REFERENCE_PARAMS).
    Derived from DetectedIssueModel.content — never read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain string, not a
    Postgres enum (`implicated` is Reference(Any); a search by bare id is ambiguous).

      <param>             -> reference_type/reference_id or reference_reference
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` and no UniqueConstraint: R4 does not forbid listing the
    same reference twice."""

    __tablename__ = "detected_issue_reference"
    __table_args__ = (Index("ix_detected_issue_reference_param_type_id", "param", "reference_type", "reference_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_pk = Column(BigInteger, ForeignKey("detected_issue.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    detected_issue = relationship("DetectedIssueModel", back_populates="references")
