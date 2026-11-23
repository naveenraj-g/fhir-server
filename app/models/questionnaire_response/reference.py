from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a QuestionnaireResponseReference row feeds, the QuestionnaireResponse
# element it is read from, and the resource types that element points at (R4: basedOn ->
# CarePlan | ServiceRequest; partOf -> Observation | Procedure; questionnaire -> the canonical URL
# of a Questionnaire).
REFERENCE_PARAMS = {
    "based-on": "basedOn",
    "part-of": "partOf",
    "questionnaire": "questionnaire",
}
REFERENCE_TYPES = {
    "based-on": ("CarePlan", "ServiceRequest"),
    "part-of": ("Observation", "Procedure"),
    "questionnaire": ("Questionnaire",),
}

# The R4 targets of the 0..1 references held as columns on the row.
ENCOUNTER_TYPES = ("Encounter",)
AUTHOR_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Device",
    "Patient",
    "RelatedPerson",
)
SOURCE_TYPES = ("Practitioner", "Patient", "PractitionerRole", "RelatedPerson")
# `subject` is Reference(Any): the parser only accepts `:Type` for a declared target, so list the
# types a subject can realistically be. A relative reference to a type not listed is still indexed
# (and found by its absolute URL).
SUBJECT_TYPES = (
    "Patient",
    "Group",
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
    "MedicationStatement",
    "MedicationAdministration",
    "CarePlan",
    "CareTeam",
    "Specimen",
    "Device",
)


class QuestionnaireResponseReference(Base):
    """Search index for the repeating / canonical reference parameters `based-on`, `part-of` and
    `questionnaire`: one row per Reference (or canonical URL) that has a value (one with only
    `display` cannot be matched by a reference search). `param` says which search parameter the
    row belongs to (see REFERENCE_PARAMS). Derived from QuestionnaireResponseModel.content - never
    read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string, not
    a Postgres enum. `based-on` and `part-of` have two targets each (a search by bare id is
    ambiguous: `based-on=Type/id` or `:Type=id`); `questionnaire` has one, but holds a canonical
    URL, so its rows are usually just the raw string (a versioned `url|1.0` is matched by the
    unversioned `url` too).

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL / canonical)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same reference twice."""

    __tablename__ = "questionnaire_response_reference"
    __table_args__ = (
        Index(
            "ix_questionnaire_response_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_response_pk = Column(
        BigInteger, ForeignKey("questionnaire_response.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    questionnaire_response = relationship(
        "QuestionnaireResponseModel", back_populates="references"
    )
