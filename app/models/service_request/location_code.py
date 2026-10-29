from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# locationCode (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ServiceRequestLocationCode(TenantAuditMixin, Base):
    """One entry of ServiceRequest.locationCode (0..* CodeableConcept) —
    coded location, as opposed to locationReference's resolved Location."""

    __tablename__ = "service_request_location_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    service_request = relationship("ServiceRequestModel", back_populates="location_codes")
    codings = relationship(
        "ServiceRequestLocationCodeCoding", back_populates="location_code", cascade="all, delete-orphan"
    )


class ServiceRequestLocationCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.locationCode.coding (0..*)."""

    __tablename__ = "service_request_location_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_location_code_id = Column(
        BigInteger, ForeignKey("service_request_location_code.id"), nullable=False, index=True
    )

    location_code = relationship("ServiceRequestLocationCode", back_populates="codings")
