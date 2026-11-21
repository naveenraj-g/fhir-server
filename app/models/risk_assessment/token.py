from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in RiskAssessmentToken, and the element each reads
# (`risk` reads prediction.qualitativeRisk of every prediction).
TOKEN_PARAMS = {
    "method": "method",
    "risk": "prediction.qualitativeRisk",
}


class RiskAssessmentToken(Base):
    """Search index for the two CodeableConcept token parameters (`method`, `risk`): one row
    per coding of each concept — a token search matches any coding of any prediction — plus
    one code-less row for a concept with only `text`, so `:text` still finds it. `param` says
    which search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    RiskAssessmentModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of two identical ones."""

    __tablename__ = "risk_assessment_token"
    __table_args__ = (Index("ix_risk_assessment_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_pk = Column(
        BigInteger, ForeignKey("risk_assessment.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    risk_assessment = relationship("RiskAssessmentModel", back_populates="tokens")
