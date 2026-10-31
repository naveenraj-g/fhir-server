from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.allergy_intolerance.enums import (
    AllergyIntoleranceNoteAuthorReferenceType,
)
from app.models.shared import TenantAuditMixin


class AllergyIntoleranceNote(TenantAuditMixin, Base):
    """AllergyIntolerance.note (0..* Annotation) child table."""

    __tablename__ = "allergy_intolerance_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    allergy_intolerance_pk = Column(
        BigInteger,
        ForeignKey("allergy_intolerance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    text = Column(Text, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    author_string = Column(String, nullable=True)
    author_reference_type = Column(
        Enum(
            AllergyIntoleranceNoteAuthorReferenceType,
            name="allergy_intolerance_note_author_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    author_reference_id = Column(BigInteger, nullable=True)
    author_reference_display = Column(String, nullable=True)

    allergy_intolerance = relationship(
        "AllergyIntoleranceModel",
        back_populates="notes",
    )
