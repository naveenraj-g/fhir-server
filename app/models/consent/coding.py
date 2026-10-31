from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConsentScopeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.scope.coding (0..* Coding) child table."""

    __tablename__ = "consent_scope_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id", ondelete="CASCADE"), nullable=False, index=True
    )

    consent = relationship("ConsentModel", back_populates="scope_codings")


class ConsentPolicyRuleCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.policyRule.coding (0..* Coding) child table."""

    __tablename__ = "consent_policy_rule_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id", ondelete="CASCADE"), nullable=False, index=True
    )

    consent = relationship("ConsentModel", back_populates="policy_rule_codings")
