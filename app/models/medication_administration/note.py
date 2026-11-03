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
from app.models.medication_administration.enums import (
    MedicationAdministrationNoteAuthorReferenceType,
)
from app.models.shared import TenantAuditMixin


class MedicationAdministrationNote(TenantAuditMixin, Base):
    """MedicationAdministration.note (0..* Annotation) child table."""

    __tablename__ = "medication_administration_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    text = Column(Text, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            MedicationAdministrationNoteAuthorReferenceType,
            name="medication_administration_note_author_reference_type",
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    # Reference.identifier fallback (11 columns)
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

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="notes"
    )
