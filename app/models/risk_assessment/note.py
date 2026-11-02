from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.risk_assessment.enums import RiskAssessmentNoteAuthorReferenceType
from app.models.shared import TenantAuditMixin


class RiskAssessmentNoteModel(TenantAuditMixin, Base):
    """RiskAssessment.note (0..* Annotation) child table."""

    __tablename__ = "risk_assessment_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_pk = Column(
        BigInteger, ForeignKey("risk_assessment.id"), nullable=False, index=True
    )

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            RiskAssessmentNoteAuthorReferenceType,
            name="risk_assessment_note_author_reference_type",
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

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

    time = Column(DateTime(timezone=True), nullable=True)
    text = Column(Text, nullable=False)

    risk_assessment = relationship(
        "RiskAssessmentModel", back_populates="notes"
    )
