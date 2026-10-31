from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.care_team.enums import CareTeamNoteAuthorReferenceType
from app.models.shared import TenantAuditMixin


class CareTeamNote(TenantAuditMixin, Base):
    """CareTeam.note (0..*) Annotation child table."""

    __tablename__ = "care_team_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )

    text = Column(String, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    author_string = Column(String, nullable=True)
    author_reference_reference = Column(String, nullable=True)
    author_reference_type = Column(
        Enum(
            CareTeamNoteAuthorReferenceType,
            name="care_team_note_author_reference_type",
        ),
        nullable=True,
    )
    author_reference_id = Column(BigInteger, nullable=True, index=True)
    author_reference_display = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="notes")
