from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin


class CommunicationNote(TenantAuditMixin, Base):
    """Communication.note (0..*) Annotation child table."""

    __tablename__ = "communication_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(String, nullable=True)
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)
    time = Column(DateTime(timezone=True), nullable=True)
    text = Column(Text, nullable=False)

    communication = relationship(
        "CommunicationModel", back_populates="notes"
    )
