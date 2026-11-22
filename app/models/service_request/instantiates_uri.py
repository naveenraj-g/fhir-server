from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class ServiceRequestInstantiatesUri(Base):
    """Search index for `instantiates-uri` (ServiceRequest.instantiatesUri, 0..* uri):
    one row per URI. A `uri` search matches exactly (case-sensitive); `:below`
    matches stored URIs that start with the value and `:above` stored URIs that
    are a prefix of it. Derived from ServiceRequestModel.content — never read to build
    a response."""

    __tablename__ = "service_request_instantiates_uri"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )
    uri = Column(String, nullable=False, index=True)

    service_request = relationship(
        "ServiceRequestModel", back_populates="instantiates_uris"
    )
