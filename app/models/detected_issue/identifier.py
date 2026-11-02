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
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class DetectedIssueIdentifierModel(TenantAuditMixin, Base):
    """DetectedIssue.identifier (0..* Identifier) child table."""

    __tablename__ = "detected_issue_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_pk = Column(
        BigInteger, ForeignKey("detected_issue.id"), nullable=False, index=True
    )

    use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization))
    assigner_reference = Column(String, nullable=True)
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_display = Column(String, nullable=True)

    # assigner.identifier fallback (11 columns)
    assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    assigner_identifier_type_system = Column(String, nullable=True)
    assigner_identifier_type_version = Column(String, nullable=True)
    assigner_identifier_type_code = Column(String, nullable=True)
    assigner_identifier_type_display = Column(String, nullable=True)
    assigner_identifier_type_user_selected = Column(Boolean, nullable=True)
    assigner_identifier_type_text = Column(String, nullable=True)
    assigner_identifier_system = Column(String, nullable=True)
    assigner_identifier_value = Column(String, nullable=True)
    assigner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    assigner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    detected_issue = relationship(
        "DetectedIssueModel", back_populates="identifiers"
    )
    type_codings = relationship(
        "DetectedIssueIdentifierTypeCodingModel",
        back_populates="identifier",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DetectedIssueIdentifierTypeCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """detected_issue_identifier.type.coding (0..* Coding) grandchild table."""

    __tablename__ = "detected_issue_identifier_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_identifier_id = Column(
        BigInteger,
        ForeignKey("detected_issue_identifier.id"),
        nullable=False,
        index=True,
    )

    identifier = relationship(
        "DetectedIssueIdentifierModel", back_populates="type_codings"
    )
