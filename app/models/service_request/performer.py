from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The eight R4 targets of ServiceRequest.performer.
PERFORMER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "CareTeam",
    "HealthcareService",
    "Patient",
    "Device",
    "RelatedPerson",
)


class ServiceRequestPerformer(Base):
    """Search index for `performer` (ServiceRequest.performer, 0..* References): one row per performer with a
    `reference` or an `identifier`. Derived from ServiceRequestModel.content — never
    read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain
    string, not a Postgres enum, because a performer can be one of eight types (a
    search by bare id is ambiguous: `performer=Type/id` or `:Type=id`).

      performer             -> reference_type/reference_id or reference_reference
      performer:identifier  -> reference_identifier_system/_value
    """

    __tablename__ = "service_request_performer"
    __table_args__ = (
        Index("ix_service_request_performer_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    service_request = relationship("ServiceRequestModel", back_populates="performers")
