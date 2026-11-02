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

from .enums import DetectedIssueMitigationAuthorReferenceType


class DetectedIssueMitigationModel(TenantAuditMixin, Base):
    """DetectedIssue.mitigation (0..* BackboneElement) child table."""

    __tablename__ = "detected_issue_mitigation"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_pk = Column(
        BigInteger, ForeignKey("detected_issue.id"), nullable=False, index=True
    )

    action_text = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)

    # author (0..1 Reference(Practitioner | PractitionerRole))
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            DetectedIssueMitigationAuthorReferenceType,
            name="detected_issue_mitigation_author_reference_type",
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    # author.identifier fallback (11 columns)
    author_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    author_identifier_type_system = Column(String, nullable=True)
    author_identifier_type_version = Column(String, nullable=True)
    author_identifier_type_code = Column(String, nullable=True)
    author_identifier_type_display = Column(String, nullable=True)
    author_identifier_type_user_selected = Column(Boolean, nullable=True)
    author_identifier_type_text = Column(String, nullable=True)
    author_identifier_system = Column(String, nullable=True)
    author_identifier_value = Column(String, nullable=True)
    author_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    author_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    detected_issue = relationship("DetectedIssueModel", back_populates="mitigations")
    action_codings = relationship(
        "DetectedIssueMitigationActionCodingModel",
        back_populates="mitigation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DetectedIssueMitigationActionCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """detected_issue_mitigation.action.coding (0..* Coding) grandchild table."""

    __tablename__ = "detected_issue_mitigation_action_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_mitigation_id = Column(
        BigInteger,
        ForeignKey("detected_issue_mitigation.id"),
        nullable=False,
        index=True,
    )

    mitigation = relationship(
        "DetectedIssueMitigationModel", back_populates="action_codings"
    )
