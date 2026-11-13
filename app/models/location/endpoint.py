from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.location.enums import LocationEndpointReferenceType


class LocationEndpoint(Base):
    """Search index for the `endpoint` reference parameter (0..*): one row
    per Location.endpoint that has a `reference` or an `identifier` — same
    shape as OrganizationEndpoint. Derived from LocationModel.content —
    never read to build a response.

    No UniqueConstraint: R4 doesn't forbid listing the same endpoint twice."""

    __tablename__ = "location_endpoint"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(LocationEndpointReferenceType, name="location_endpoint_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    location = relationship("LocationModel", back_populates="endpoints")
