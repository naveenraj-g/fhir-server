from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# referralMethod (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class HealthcareServiceReferralMethod(TenantAuditMixin, Base):
    """referralMethod[] — ways that the service accepts referrals. `text`
    stays flattened (sibling of coding[], not part of it); `coding[]`
    itself is a real 0..* child table (HealthcareServiceReferralMethodCoding,
    below) rather than a single flattened coding — same reasoning as
    OrganizationType's own coding[] promotion."""

    __tablename__ = "healthcare_service_referral_method"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="referral_methods"
    )
    codings = relationship(
        "HealthcareServiceReferralMethodCoding",
        back_populates="referral_method",
        cascade="all, delete-orphan",
    )


class HealthcareServiceReferralMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.referralMethod.coding (0..*)."""

    __tablename__ = "healthcare_service_referral_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_referral_method_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_referral_method.id"),
        nullable=False,
        index=True,
    )

    referral_method = relationship(
        "HealthcareServiceReferralMethod", back_populates="codings"
    )
