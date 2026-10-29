from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# category (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ServiceRequestCategory(TenantAuditMixin, Base):
    """One entry of ServiceRequest.category (0..* CodeableConcept). `text`
    stays flattened (sibling of coding[], not part of it); `coding[]`
    itself is a real 0..* grandchild table (ServiceRequestCategoryCoding,
    below)."""

    __tablename__ = "service_request_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    service_request = relationship("ServiceRequestModel", back_populates="categories")
    codings = relationship(
        "ServiceRequestCategoryCoding", back_populates="category", cascade="all, delete-orphan"
    )


class ServiceRequestCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.category.coding (0..*)."""

    __tablename__ = "service_request_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_category_id = Column(
        BigInteger, ForeignKey("service_request_category.id"), nullable=False, index=True
    )

    category = relationship("ServiceRequestCategory", back_populates="codings")
