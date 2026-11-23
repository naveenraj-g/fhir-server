from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The R4 targets of each reference element a MedicationAdministration search parameter reads.
SUBJECT_TYPES = ("Patient", "Group")
CONTEXT_TYPES = ("Encounter", "EpisodeOfCare")
MEDICATION_TYPES = ("Medication",)
REQUEST_TYPES = ("MedicationRequest",)

# Which search parameter a MedicationAdministrationReference row feeds, the element it is read
# from, and the resource types that element points at.
REFERENCE_PARAMS = {"device": "device", "performer": "performer.actor"}
REFERENCE_TYPES = {
    "device": ("Device",),
    "performer": (
        "Practitioner",
        "PractitionerRole",
        "Patient",
        "RelatedPerson",
        "Device",
    ),
}


class MedicationAdministrationReference(Base):
    """Search index for the repeating reference parameters `device` and `performer`: one row per
    Reference that has a value (one with only `display` cannot be matched by a reference
    search). `param` says which search parameter the row belongs to (see REFERENCE_PARAMS).
    Derived from MedicationAdministrationModel.content - never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string,
    not a Postgres enum. `performer` has five targets, so a search by bare id is ambiguous
    (`performer=Type/id` or `performer:Type=id`); `device` has one.

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system / _value (a logical reference)"""

    __tablename__ = "medication_administration_reference"
    __table_args__ = (
        Index(
            "ix_medication_administration_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger,
        ForeignKey("medication_administration.id"),
        nullable=False,
        index=True,
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="references"
    )
