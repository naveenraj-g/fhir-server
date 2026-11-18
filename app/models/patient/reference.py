from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a PatientReference row feeds, the Patient element it is
# read from, and the resource types that element can point at (R4:
# generalPractitioner -> Organization | Practitioner | PractitionerRole,
# link.other -> Patient | RelatedPerson).
REFERENCE_PARAMS = {
    "general-practitioner": "generalPractitioner",
    "link": "link",
}
GENERAL_PRACTITIONER_TYPES = ("Organization", "Practitioner", "PractitionerRole")
LINK_TYPES = ("Patient", "RelatedPerson")
REFERENCE_TYPES = {
    "general-practitioner": GENERAL_PRACTITIONER_TYPES,
    "link": LINK_TYPES,
}


class PatientReference(Base):
    """Search index for the two 0..* reference parameters
    `general-practitioner` and `link`: one row per Reference that has a
    `reference` or an `identifier` (one with only `display` can't be matched
    by a reference search). `param` says which search parameter the row
    belongs to (see REFERENCE_PARAMS). Derived from PatientModel.content —
    never read to build a response.

    Both can point at several resource types, so `reference_type` records
    which one a relative `Type/<id>` names — a search by bare id is ambiguous
    and R4 requires a type (`general-practitioner=Type/id` or
    `general-practitioner:Type=id`).

      <param>             -> reference_type/reference_id (a relative
                             Type/<id>) or reference_reference (the raw
                             string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    `reference_type` is a plain string, not a Postgres enum, and there is no
    ForeignKey on `reference_id` (the public id of another resource) and no
    UniqueConstraint: R4 doesn't forbid listing the same reference twice."""

    __tablename__ = "patient_reference"
    __table_args__ = (Index("ix_patient_reference_param_type_id", "param", "reference_type", "reference_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(BigInteger, ForeignKey("patient.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="references")
