from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# bodySite (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ServiceRequestBodySite(TenantAuditMixin, Base):
    """One entry of ServiceRequest.bodySite (0..* CodeableConcept)."""

    __tablename__ = "service_request_body_site"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    service_request = relationship("ServiceRequestModel", back_populates="body_sites")
    codings = relationship(
        "ServiceRequestBodySiteCoding", back_populates="body_site", cascade="all, delete-orphan"
    )


class ServiceRequestBodySiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.bodySite.coding (0..*)."""

    __tablename__ = "service_request_body_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_body_site_id = Column(
        BigInteger, ForeignKey("service_request_body_site.id"), nullable=False, index=True
    )

    body_site = relationship("ServiceRequestBodySite", back_populates="codings")
