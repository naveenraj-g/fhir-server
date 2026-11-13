from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.organization.enums import OrganizationEndpointReferenceType


class OrganizationEndpoint(Base):
    """Search index for the `endpoint` reference parameter (0..*): one row
    per Organization.endpoint that has a `reference` or an `identifier`
    (one with only `display` can't be matched by a reference search).
    Derived from OrganizationModel.content — never read to build a response.

      endpoint             -> reference_type/reference_id (relative Endpoint/<id>)
                              or reference_reference (the raw string, for
                              an absolute URL)
      endpoint:identifier  -> reference_identifier_system/_value

    No UniqueConstraint: R4 doesn't forbid listing the same endpoint twice."""

    __tablename__ = "organization_endpoint"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(OrganizationEndpointReferenceType, name="organization_endpoint_ref_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    organization = relationship("OrganizationModel", back_populates="endpoints")
