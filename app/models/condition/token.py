from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ConditionToken, and the Condition element each reads
# (`evidence` -> evidence.code, `stage` -> stage.summary, `body-site` ->
# bodySite; the rest read the element of the same name).
TOKEN_PARAMS = {
    "body-site": "bodySite",
    "category": "category",
    "clinical-status": "clinicalStatus",
    "code": "code",
    "evidence": "evidence.code",
    "severity": "severity",
    "stage": "stage.summary",
    "verification-status": "verificationStatus",
}


class ConditionToken(Base):
    """Search index for the eight CodeableConcept token parameters
    (`body-site`, `category`, `clinical-status`, `code`, `evidence`,
    `severity`, `stage`, `verification-status`): one row per coding of each
    concept — a token search matches any coding of any entry — plus one
    code-less row for a concept with only `text`, so `:text` still finds it.
    `param` says which search parameter the row belongs to (see TOKEN_PARAMS).
    Derived from ConditionModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of eight identical ones."""

    __tablename__ = "condition_token"
    __table_args__ = (Index("ix_condition_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    condition = relationship("ConditionModel", back_populates="tokens")
