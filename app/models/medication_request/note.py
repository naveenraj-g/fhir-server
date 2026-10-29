from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.medication_request.enums import MedicationRequestNoteAuthorReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# note (0..*) Annotation child table — mirrors
# app.models.service_request.note.ServiceRequestNote field-for-field.
# ---------------------------------------------------------------------------


class MedicationRequestNote(TenantAuditMixin, Base):
    """MedicationRequest.note (0..* Annotation)."""

    __tablename__ = "medication_request_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(MedicationRequestNoteAuthorReferenceType, name="medication_request_note_author_reference_type"),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    time = Column(DateTime(timezone=True), nullable=True)
    text = Column(Text, nullable=True)

    medication_request = relationship("MedicationRequestModel", back_populates="notes")
