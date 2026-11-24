from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ConsentToken, and the Consent element each reads (`action`, `purpose`
# and `security-label` read the top-level `provision`).
TOKEN_PARAMS = {
    "category": "category",
    "scope": "scope",
    "action": "provision.action",
    "purpose": "provision.purpose",
    "security-label": "provision.securityLabel",
}


class ConsentToken(Base):
    """Search index for the five token parameters (see TOKEN_PARAMS): one row per coding of each
    CodeableConcept (or per Coding, for `purpose` and `security-label`) - a token search matches
    any coding of any entry - plus one code-less row for a concept with only `text`, so `:text`
    still finds it. `param` says which search parameter the row belongs to. Derived from
    ConsentModel.content - never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "consent_token"
    __table_args__ = (Index("ix_consent_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    consent = relationship("ConsentModel", back_populates="tokens")
