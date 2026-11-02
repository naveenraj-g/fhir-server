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
from app.models.family_member_history.enums import FamilyMemberHistoryNoteAuthorReferenceType
from app.models.shared import TenantAuditMixin


class FamilyMemberHistoryNote(TenantAuditMixin, Base):
    """FamilyMemberHistory.note (0..* Annotation)."""

    __tablename__ = "family_member_history_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_pk = Column(
        BigInteger, ForeignKey("family_member_history.id"), nullable=False, index=True
    )

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            FamilyMemberHistoryNoteAuthorReferenceType,
            name="family_member_history_note_author_reference_type",
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

    time = Column(DateTime(timezone=True), nullable=True)
    text = Column(Text, nullable=True)

    family_member_history = relationship(
        "FamilyMemberHistoryModel", back_populates="notes"
    )
