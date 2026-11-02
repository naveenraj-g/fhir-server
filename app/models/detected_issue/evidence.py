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
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class DetectedIssueEvidenceModel(TenantAuditMixin, Base):
    """DetectedIssue.evidence (0..* BackboneElement) child table."""

    __tablename__ = "detected_issue_evidence"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_pk = Column(
        BigInteger, ForeignKey("detected_issue.id"), nullable=False, index=True
    )

    detected_issue = relationship("DetectedIssueModel", back_populates="evidence_list")
    codes = relationship(
        "DetectedIssueEvidenceCodeModel",
        back_populates="evidence",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    details = relationship(
        "DetectedIssueEvidenceDetailModel",
        back_populates="evidence",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DetectedIssueEvidenceCodeModel(TenantAuditMixin, Base):
    """detected_issue_evidence.code (0..* CodeableConcept) grandchild table."""

    __tablename__ = "detected_issue_evidence_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_evidence_id = Column(
        BigInteger,
        ForeignKey("detected_issue_evidence.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    evidence = relationship("DetectedIssueEvidenceModel", back_populates="codes")
    codings = relationship(
        "DetectedIssueEvidenceCodeCodingModel",
        back_populates="evidence_code",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DetectedIssueEvidenceCodeCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """detected_issue_evidence_code.coding (0..* Coding) great-grandchild table."""

    __tablename__ = "detected_issue_evidence_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_evidence_code_id = Column(
        BigInteger,
        ForeignKey("detected_issue_evidence_code.id"),
        nullable=False,
        index=True,
    )

    evidence_code = relationship(
        "DetectedIssueEvidenceCodeModel", back_populates="codings"
    )


class DetectedIssueEvidenceDetailModel(TenantAuditMixin, Base):
    """detected_issue_evidence.detail (0..* Reference(Any)) grandchild table."""

    __tablename__ = "detected_issue_evidence_detail"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_evidence_id = Column(
        BigInteger,
        ForeignKey("detected_issue_evidence.id"),
        nullable=False,
        index=True,
    )

    detail_reference = Column(String, nullable=True)
    detail_type = Column(String, nullable=True)
    detail_id = Column(BigInteger, nullable=True, index=True)
    detail_display = Column(String, nullable=True)

    # detail.identifier fallback (11 columns)
    detail_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    detail_identifier_type_system = Column(String, nullable=True)
    detail_identifier_type_version = Column(String, nullable=True)
    detail_identifier_type_code = Column(String, nullable=True)
    detail_identifier_type_display = Column(String, nullable=True)
    detail_identifier_type_user_selected = Column(Boolean, nullable=True)
    detail_identifier_type_text = Column(String, nullable=True)
    detail_identifier_system = Column(String, nullable=True)
    detail_identifier_value = Column(String, nullable=True)
    detail_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    detail_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    evidence = relationship("DetectedIssueEvidenceModel", back_populates="details")
