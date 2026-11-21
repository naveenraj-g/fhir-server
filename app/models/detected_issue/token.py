from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in DetectedIssueToken, and the element each reads.
TOKEN_PARAMS = {
    "code": "code",
}


class DetectedIssueToken(Base):
    """Search index for the CodeableConcept token parameter `code`: one row per coding
    of the 0..1 `code` — plus one code-less row for a concept with only `text`, so `:text` still finds
    it. `param` says which search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    DetectedIssueModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    A shared table (with a `param` column) like the other content-based resources, even though
    only one parameter lives here today."""

    __tablename__ = "detected_issue_token"
    __table_args__ = (Index("ix_detected_issue_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    detected_issue_pk = Column(
        BigInteger, ForeignKey("detected_issue.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    detected_issue = relationship("DetectedIssueModel", back_populates="tokens")
