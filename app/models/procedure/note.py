from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.procedure.enums import ProcedureAuthorReferenceType
from app.models.shared import TenantAuditMixin


class ProcedureNote(TenantAuditMixin, Base):
    """Procedure.note (0..* Annotation) child table."""

    __tablename__ = "procedure_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    text = Column(String, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    author_string = Column(String, nullable=True)
    author_reference_reference = Column(String, nullable=True)
    author_reference_type = Column(
        Enum(
            ProcedureAuthorReferenceType,
            name="procedure_author_reference_type",
        ),
        nullable=True,
    )
    author_reference_id = Column(BigInteger, nullable=True, index=True)
    author_reference_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="notes")
