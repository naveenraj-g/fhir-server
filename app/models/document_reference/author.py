from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.document_reference.enums import DocumentReferenceAuthorReferenceType
from app.models.shared import TenantAuditMixin


class DocumentReferenceAuthor(TenantAuditMixin, Base):
    """DocumentReference.author (0..*) child table."""

    __tablename__ = "document_reference_author"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            DocumentReferenceAuthorReferenceType,
            name="document_reference_author_reference_type",
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="authors")
