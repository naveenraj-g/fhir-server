from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ClinicalImpressionToken, and the element each reads.
TOKEN_PARAMS = {
    "finding-code": "finding.itemCodeableConcept",
}


class ClinicalImpressionToken(Base):
    """Search index for the CodeableConcept token parameter `finding-code`: one row per coding
    of `finding.itemCodeableConcept` of *every* finding — a token search matches any coding of
    any finding — plus one code-less row for a concept with only `text`, so `:text` still finds
    it. `param` says which search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    ClinicalImpressionModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    A shared table (with a `param` column) like the other content-based resources, even though
    only one parameter lives here today."""

    __tablename__ = "clinical_impression_token"
    __table_args__ = (Index("ix_clinical_impression_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    clinical_impression = relationship("ClinicalImpressionModel", back_populates="tokens")
