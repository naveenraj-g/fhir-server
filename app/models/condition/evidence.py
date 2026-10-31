from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConditionEvidence(TenantAuditMixin, Base):
    """One entry of Condition.evidence (0..* BackboneElement)."""

    __tablename__ = "condition_evidence"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )

    condition = relationship("ConditionModel", back_populates="evidence")
    codes = relationship(
        "ConditionEvidenceCode",
        back_populates="evidence",
        cascade="all, delete-orphan",
    )
    details = relationship(
        "ConditionEvidenceDetail",
        back_populates="evidence",
        cascade="all, delete-orphan",
    )


class ConditionEvidenceCode(TenantAuditMixin, Base):
    """One entry of Condition.evidence.code (0..* CodeableConcept)."""

    __tablename__ = "condition_evidence_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_evidence_id = Column(
        BigInteger, ForeignKey("condition_evidence.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    evidence = relationship("ConditionEvidence", back_populates="codes")
    codings = relationship(
        "ConditionEvidenceCodeCoding",
        back_populates="evidence_code",
        cascade="all, delete-orphan",
    )


class ConditionEvidenceCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Condition.evidence.code.coding (0..*)."""

    __tablename__ = "condition_evidence_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_evidence_code_id = Column(
        BigInteger,
        ForeignKey("condition_evidence_code.id"),
        nullable=False,
        index=True,
    )

    evidence_code = relationship("ConditionEvidenceCode", back_populates="codings")


class ConditionEvidenceDetail(TenantAuditMixin, Base):
    """One entry of Condition.evidence.detail (0..* Reference(Any))."""

    __tablename__ = "condition_evidence_detail"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_evidence_id = Column(
        BigInteger, ForeignKey("condition_evidence.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # Reference identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)

    evidence = relationship("ConditionEvidence", back_populates="details")
