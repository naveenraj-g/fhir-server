from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in DocumentReferenceToken, and the element each reads. All are
# CodeableConcept elements: `type` (0..1), `category` (0..*), `security-label` (0..*), `event`
# (context.event, 0..*), `facility` (context.facilityType, 0..1) and `setting`
# (context.practiceSetting, 0..1). (`format` - content.format, a bare Coding on every content
# entry - is held with the rest of the content entry, in DocumentReferenceContent.)
TOKEN_PARAMS = {
    "type": "type",
    "category": "category",
    "security-label": "securityLabel",
    "event": "context.event",
    "facility": "context.facilityType",
    "setting": "context.practiceSetting",
}


class DocumentReferenceToken(Base):
    """Search index for the token parameters held in one shared table (see TOKEN_PARAMS): one row
    per coding of each concept - a token search matches any coding - plus one code-less row for a
    concept with only `text`, so `:text` still finds it. `param` says which search parameter the
    row belongs to. Derived from DocumentReferenceModel.content - never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    None of these elements has a required binding, so they are strings, not enums (a profile may
    add codes)."""

    __tablename__ = "document_reference_token"
    __table_args__ = (Index("ix_document_reference_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="tokens")
