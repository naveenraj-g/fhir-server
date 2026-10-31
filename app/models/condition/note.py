from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.condition.enums import ConditionNoteAuthorReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin


class ConditionNote(TenantAuditMixin, Base):
    """Condition.note (0..* Annotation)."""

    __tablename__ = "condition_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            ConditionNoteAuthorReferenceType,
            name="condition_note_author_reference_type",
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    # Reference identifier fallback
    author_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    author_identifier_system = Column(String, nullable=True)
    author_identifier_value = Column(String, nullable=True)
    author_identifier_type_text = Column(String, nullable=True)

    time = Column(DateTime(timezone=True), nullable=True)
    text = Column(Text, nullable=True)

    condition = relationship("ConditionModel", back_populates="notes")
