from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.consent.enums import (
    ConsentPerformerReferenceType,
    ConsentVerifiedWithReferenceType,
)
from app.models.enums import OrganizationReferenceType
from app.models.shared import TenantAuditMixin


class ConsentPerformer(TenantAuditMixin, Base):
    """Consent.performer (0..* Reference) child table."""

    __tablename__ = "consent_performer"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=False)
    reference_type = Column(
        Enum(
            ConsentPerformerReferenceType,
            name="consent_performer_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True)
    reference_display = Column(String, nullable=True)

    consent = relationship("ConsentModel", back_populates="performers")


class ConsentOrganization(TenantAuditMixin, Base):
    """Consent.organization (0..* Reference(Organization)) child table."""

    __tablename__ = "consent_organization"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=False)
    reference_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
            create_type=False,
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True)
    reference_display = Column(String, nullable=True)

    consent = relationship("ConsentModel", back_populates="organizations")


class ConsentPolicy(TenantAuditMixin, Base):
    """Consent.policy (0..* BackboneElement) child table."""

    __tablename__ = "consent_policy"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id", ondelete="CASCADE"), nullable=False, index=True
    )

    authority = Column(String, nullable=True)
    uri = Column(String, nullable=True)

    consent = relationship("ConsentModel", back_populates="policies")


class ConsentVerification(TenantAuditMixin, Base):
    """Consent.verification (0..* BackboneElement) child table."""

    __tablename__ = "consent_verification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id", ondelete="CASCADE"), nullable=False, index=True
    )

    verified = Column(Boolean, nullable=False)
    verified_with_reference = Column(String, nullable=True)
    verified_with_type = Column(
        Enum(
            ConsentVerifiedWithReferenceType,
            name="consent_verified_with_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    verified_with_id = Column(BigInteger, nullable=True)
    verified_with_display = Column(String, nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)

    consent = relationship("ConsentModel", back_populates="verifications")
