from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# orderDetail (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ServiceRequestOrderDetail(TenantAuditMixin, Base):
    """One entry of ServiceRequest.orderDetail (0..* CodeableConcept).
    Invariant: per the FHIR spec, orderDetail SHALL only be present if
    `code` is present — enforced by the validator layer, not a DB
    constraint, same as every other structural R4 rule in this codebase."""

    __tablename__ = "service_request_order_detail"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    service_request = relationship("ServiceRequestModel", back_populates="order_details")
    codings = relationship(
        "ServiceRequestOrderDetailCoding", back_populates="order_detail", cascade="all, delete-orphan"
    )


class ServiceRequestOrderDetailCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.orderDetail.coding (0..*)."""

    __tablename__ = "service_request_order_detail_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_order_detail_id = Column(
        BigInteger, ForeignKey("service_request_order_detail.id"), nullable=False, index=True
    )

    order_detail = relationship("ServiceRequestOrderDetail", back_populates="codings")
