from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared.resource_types import ANY_RESOURCE_TYPES

# Which search parameter a CommunicationReference row feeds and the Communication element it is
# read from.
REFERENCE_PARAMS = {
    "based-on": "basedOn",
    "part-of": "partOf",
    "recipient": "recipient",
    "instantiates-canonical": "instantiatesCanonical",
}
# R4 targets of each parameter. `basedOn` and `partOf` are Reference(Any): R4 allows every resource
# type, so the whole R4 list is the target (the shared tuple: `is_any()` checks identity).
BASED_ON_TYPES = ANY_RESOURCE_TYPES
PART_OF_TYPES = ANY_RESOURCE_TYPES
RECIPIENT_TYPES = (
    "Device",
    "Organization",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Group",
    "CareTeam",
    "HealthcareService",
)
CANONICAL_TYPES = (
    "PlanDefinition",
    "ActivityDefinition",
    "Measure",
    "OperationDefinition",
    "Questionnaire",
)
REFERENCE_TYPES = {
    "based-on": BASED_ON_TYPES,
    "part-of": PART_OF_TYPES,
    "recipient": RECIPIENT_TYPES,
    "instantiates-canonical": CANONICAL_TYPES,
}


class CommunicationReference(Base):
    """Search index for the `based-on`, `part-of`, `recipient` and `instantiates-canonical`
    reference parameters: one row per Reference (or canonical URL) that has a value (one with only
    `display` cannot be matched by a reference search). `param` says which search parameter the
    row belongs to (see REFERENCE_PARAMS). Derived from CommunicationModel.content - never read to
    build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string,
    not a Postgres enum. `instantiates-canonical` holds canonical URLs, so its rows are usually
    just the raw string (a versioned `url|1.0` is matched by the unversioned `url` too).

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same reference twice."""

    __tablename__ = "communication_reference"
    __table_args__ = (
        Index(
            "ix_communication_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger, ForeignKey("communication.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    communication = relationship("CommunicationModel", back_populates="references")
