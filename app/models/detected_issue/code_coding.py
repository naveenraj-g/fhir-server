from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class DetectedIssueCodeCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """DetectedIssue.code.coding (0..* Coding) child table."""

    __tablename__ = "detected_issue_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_pk = Column(
        BigInteger, ForeignKey("detected_issue.id"), nullable=False, index=True
    )

    detected_issue = relationship("DetectedIssueModel", back_populates="code_codings")
