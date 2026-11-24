from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared.resource_types import ANY_RESOURCE_TYPES

# Which search parameter a CommunicationRequestReference row feeds and the CommunicationRequest element it is
# read from.
REFERENCE_PARAMS = {
    "based-on": "basedOn",
    "replaces": "replaces",
    "recipient": "recipient",
}
# R4 targets of each parameter. `basedOn` is Reference(Any): R4 allows every resource
# type, so the whole R4 list is the target (the shared tuple: `is_any()` checks identity).
BASED_ON_TYPES = ANY_RESOURCE_TYPES
REPLACES_TYPES = ("CommunicationRequest",)
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
REFERENCE_TYPES = {
    "based-on": BASED_ON_TYPES,
    "replaces": REPLACES_TYPES,
    "recipient": RECIPIENT_TYPES,
}


class CommunicationRequestReference(Base):
    """Search index for the `based-on`, `replaces` and `recipient` reference parameters: one row
    per Reference that has a value (one with only
    `display` cannot be matched by a reference search). `param` says which search parameter the
    row belongs to (see REFERENCE_PARAMS). Derived from CommunicationRequestModel.content - never read to
    build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string,
    not a Postgres enum.

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same reference twice."""

    __tablename__ = "communication_request_reference"
    __table_args__ = (
        Index(
            "ix_communication_request_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger, ForeignKey("communication_request.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="references"
    )
