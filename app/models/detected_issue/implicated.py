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


class DetectedIssueImplicatedModel(TenantAuditMixin, Base):
    """DetectedIssue.implicated (0..* Reference(Any)) child table."""

    __tablename__ = "detected_issue_implicated"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_pk = Column(
        BigInteger, ForeignKey("detected_issue.id"), nullable=False, index=True
    )

    implicated_reference = Column(String, nullable=True)
    implicated_type = Column(String, nullable=True)
    implicated_id = Column(BigInteger, nullable=True, index=True)
    implicated_display = Column(String, nullable=True)

    # implicated.identifier fallback (11 columns)
    implicated_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    implicated_identifier_type_system = Column(String, nullable=True)
    implicated_identifier_type_version = Column(String, nullable=True)
    implicated_identifier_type_code = Column(String, nullable=True)
    implicated_identifier_type_display = Column(String, nullable=True)
    implicated_identifier_type_user_selected = Column(Boolean, nullable=True)
    implicated_identifier_type_text = Column(String, nullable=True)
    implicated_identifier_system = Column(String, nullable=True)
    implicated_identifier_value = Column(String, nullable=True)
    implicated_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    implicated_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    detected_issue = relationship(
        "DetectedIssueModel", back_populates="implicated_resources"
    )
