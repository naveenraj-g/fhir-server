from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.observation.enums import ObservationNoteAuthorReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# note (0..*) Annotation child table — mirrors
# app.models.medication_request.note.MedicationRequestNote field-for-field.
# ---------------------------------------------------------------------------


class ObservationNote(TenantAuditMixin, Base):
    """Observation.note (0..* Annotation)."""

    __tablename__ = "observation_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(ObservationNoteAuthorReferenceType, name="observation_note_author_reference_type"),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    time = Column(DateTime(timezone=True), nullable=True)
    text = Column(Text, nullable=True)

    observation = relationship("ObservationModel", back_populates="notes")
