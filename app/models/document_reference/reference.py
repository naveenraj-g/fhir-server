from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a DocumentReferenceReference row feeds, the DocumentReference element it
# is read from, and the resource types that element can point at (R4: author -> Practitioner |
# PractitionerRole | Organization | Device | Patient | RelatedPerson; context.encounter ->
# Encounter | EpisodeOfCare; context.related -> Reference(Any)).
REFERENCE_PARAMS = {
    "author": "author",
    "encounter": "context.encounter",
    "related": "context.related",
}
AUTHOR_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Device",
    "Patient",
    "RelatedPerson",
)
ENCOUNTER_TYPES = ("Encounter", "EpisodeOfCare")
# `related` is Reference(Any): the parser only accepts `:Type` for a declared target, so list the
# types a related resource can realistically be. A relative reference to a type not listed is
# still indexed (and found by its absolute URL).
RELATED_TYPES = (
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Organization",
    "Location",
    "HealthcareService",
    "Encounter",
    "EpisodeOfCare",
    "Appointment",
    "Condition",
    "Observation",
    "Procedure",
    "DiagnosticReport",
    "DocumentReference",
    "ServiceRequest",
    "MedicationRequest",
    "CarePlan",
    "CareTeam",
    "AllergyIntolerance",
    "Immunization",
    "FamilyMemberHistory",
    "RiskAssessment",
    "ClinicalImpression",
    "Device",
)
REFERENCE_TYPES = {
    "author": AUTHOR_TYPES,
    "encounter": ENCOUNTER_TYPES,
    "related": RELATED_TYPES,
}


class DocumentReferenceReference(Base):
    """Search index for the three repeating reference parameters `author`, `encounter`
    (context.encounter) and `related` (context.related): one row per Reference that has a value
    (one with only `display` cannot be matched by a reference search). `param` says which search
    parameter the row belongs to (see REFERENCE_PARAMS). Derived from
    DocumentReferenceModel.content - never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string, not
    a Postgres enum. `author` and `encounter` have several targets (a search by bare id is
    ambiguous: `author=Type/id` or `:Type=id`), and `related` is Reference(Any).

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same reference twice."""

    __tablename__ = "document_reference_reference"
    __table_args__ = (
        Index(
            "ix_document_reference_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    document_reference = relationship(
        "DocumentReferenceModel", back_populates="references"
    )
