from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class DocumentReferenceContent(Base):
    """Search index for `contenttype`, `language`, `location` and `format`, which read
    DocumentReference.content (1..*; each entry has an Attachment and an optional format Coding):
    one row per content entry. Derived from DocumentReferenceModel.content - never read to build a
    response.

      contenttype  -> content_type  (Attachment.contentType, a `code`: matched on the code only)
      language     -> language      (Attachment.language, a `code`: matched on the code only)
      location     -> url           (Attachment.url, a uri: exact, `:below` / `:above`)
      format       -> format_system, format_code, format_display_norm (content.format, a Coding)

    Attachment.contentType has a *required* binding to the mime-type value set, but that set is
    every BCP 13 media type (open-ended, not a list), so it is a string here, not an enum. The
    attachment's `data`, `size`, `hash`, `title` and `creation` live only in `content`."""

    __tablename__ = "document_reference_content"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )
    content_type = Column(String, nullable=True, index=True)
    language = Column(String, nullable=True)
    url = Column(String, nullable=True)
    format_system = Column(String, nullable=True)
    format_code = Column(String, nullable=True)
    format_display_norm = Column(String, nullable=True)

    document_reference = relationship(
        "DocumentReferenceModel", back_populates="contents"
    )
