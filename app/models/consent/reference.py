from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared.resource_types import ANY_RESOURCE_TYPES

# Which search parameter a ConsentReference row feeds and the Consent element it is read from
# (`actor` and `data` read the top-level `provision`).
REFERENCE_PARAMS = {
    "consentor": "performer",
    "organization": "organization",
    "actor": "provision.actor.reference",
    "data": "provision.data.reference",
}
# R4 targets of each parameter. `data` is Reference(Any): R4 allows every resource type, so the
# whole R4 list is the target (the shared tuple: `is_any()` checks identity).
CONSENTOR_TYPES = (
    "Organization",
    "Patient",
    "Practitioner",
    "RelatedPerson",
    "PractitionerRole",
)
ORGANIZATION_TYPES = ("Organization",)
ACTOR_TYPES = (
    "Device",
    "Group",
    "CareTeam",
    "Organization",
    "Patient",
    "Practitioner",
    "RelatedPerson",
    "PractitionerRole",
)
DATA_TYPES = ANY_RESOURCE_TYPES
REFERENCE_TYPES = {
    "consentor": CONSENTOR_TYPES,
    "organization": ORGANIZATION_TYPES,
    "actor": ACTOR_TYPES,
    "data": DATA_TYPES,
}


class ConsentReference(Base):
    """Search index for the `consentor`, `organization`, `actor` and `data` reference
    parameters: one row per Reference that has a value (one with only `display` cannot be matched
    by a reference search). `param` says which search parameter the row belongs to (see
    REFERENCE_PARAMS). Derived from ConsentModel.content - never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string,
    not a Postgres enum.

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same reference twice."""

    __tablename__ = "consent_reference"
    __table_args__ = (
        Index(
            "ix_consent_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    consent = relationship("ConsentModel", back_populates="references")
