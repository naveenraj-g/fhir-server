from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# reasonCode (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ServiceRequestReasonCode(TenantAuditMixin, Base):
    """One entry of ServiceRequest.reasonCode (0..* CodeableConcept) —
    coded reason, as opposed to reasonReference's resolved resource."""

    __tablename__ = "service_request_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    service_request = relationship("ServiceRequestModel", back_populates="reason_codes")
    codings = relationship(
        "ServiceRequestReasonCodeCoding", back_populates="reason_code", cascade="all, delete-orphan"
    )


class ServiceRequestReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.reasonCode.coding (0..*)."""

    __tablename__ = "service_request_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_reason_code_id = Column(
        BigInteger, ForeignKey("service_request_reason_code.id"), nullable=False, index=True
    )

    reason_code = relationship("ServiceRequestReasonCode", back_populates="codings")
